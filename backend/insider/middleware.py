import io
import sys
import time
import uuid
import json
import logging
import traceback
from typing import Dict, Any, Optional

from django.db import connection
from django.utils.deprecation import MiddlewareMixin

from insider.settings import settings as insider_settings 
from insider.settings import should_ignore_path
from insider.dispatch import dispatch_save_footprint

class LogCaptureHandler(logging.StreamHandler):
    """Custom handler to capture logs in memory."""

    def __init__(self):
        self.stream = io.StringIO()
        super().__init__(self.stream)
    
    def get_logs(self):
        # Rewind the stream, get contents, and split into lines/list
        self.stream.seek(0)

        # Return a list of strings (lines) to be saved in the JSONField
        return self.stream.getvalue().splitlines()


class FootprintMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        # Ignore paths first.
        if should_ignore_path(request.path):
            request._insider_skip = True
            return
        
        if request.method.upper() not in insider_settings.CAPTURE_METHODS:
            request._insider_skip = True
            return

        if insider_settings.CAPTURE_REQUEST_BODY and request.method in ["POST", "PUT", "PATCH"]:
            try:
                request._insider_captured_body = request.body 
            except Exception:
                request._insider_captured_body = b''

                
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # NOTE: Root configuration must be added to the documentation after the setup is complete.
        # Attach log handler for request
        handler = LogCaptureHandler()

        # Dynamically set level
        log_level = insider_settings.LOG_LEVEL.upper()
        level = getattr(logging, log_level, logging.INFO)
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        # Add handler to the root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        
        
        # Attach objects to the request
        request._insider_request_id = request_id
        request._insider_handler = handler
        request._insider_root_logger = root_logger
        request._insider_start_time = time.time()
        request._insider_initial_query_count = len(connection.queries)
        
        # Attach request ID to response header in case of exception
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response

    def process_response(self, request, response):
        if getattr(request, "_insider_skip", False):
            return response

        # Get attached objects
        handler = getattr(request, "_insider_handler", None)
        root_logger = getattr(request, "_insider_root_logger", None)
        start = getattr(request, "_insider_start_time", None)
        request_id = getattr(request, "_insider_request_id", None)

        if not (handler and root_logger and start):
            return response  # Safety fall-through if setup failed

        try:
            end = time.time()
            duration_ms = (end - start) * 1000
            db_count = len(connection.queries) - getattr(
                request, "_insider_initial_query_count", 0
            )

            self._create_footprint_record(
                request, response, duration_ms, db_count, handler, request_id
            )
        finally:
            # Cleanup handler
            root_logger.removeHandler(handler)

        return response
    
    def process_exception(self, request, exception):
        """
        Captures exception type and stack trace before Django handles it.
        """

        if getattr(request, "_insider_skip", False):
            return None
        
        request._insider_exception_name = type(exception).__name__

        # Capture Stack Trace
        _, _, exc_traceback = sys.exc_info()
        frames = traceback.extract_tb(exc_traceback)

        # Format frames into JSON-serializable list
        formatted_frames = []
        for frame in frames:
            formatted_frames.append({
                "file": frame.filename,
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line
            })

        request._insider_stack_trace = formatted_frames
        return None
        

    
    def _capture_request_body(self, request) -> Optional[Dict[str, Any]]:
        """
        Handles conditional capture, JSON parsing, and masking.
        """

        request_body = None
        
        body_bytes = getattr(request, '_insider_captured_body', None)

        if (body_bytes is not None or insider_settings.CAPTURE_REQUEST_BODY) \
            and request.method in ["POST", "PUT", "PATCH"]:
            try:
                content_type = request.META.get('CONTENT_TYPE', '').lower()
                
                if 'application/json' in content_type and body_bytes:
                    request_body = json.loads(body_bytes.decode('utf-8'))
                
                elif request.POST:
                    request_body = dict(request.POST)

                # Apply masking to sensitive fields if data was captured
                if request_body and isinstance(request_body, dict):
                    request_body = self._mask_fields(request_body)

            except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
                raw_body_str = body_bytes.decode('utf-8', errors='ignore') if body_bytes is not None else "N/A"
                request_body = {
                    "error": f"Could not parse or decode request body: {type(e).__name__}",
                    "raw_body_start": raw_body_str[:200]
                }
        
        return request_body

    def _mask_fields(self, data: Any) -> Any:
        """
        Masks sensitive fields based on insider_settings.MASK_FIELDS.
        """
        fields_to_mask = [f.lower() for f in insider_settings.MASK_FIELDS]
        mask_value = "***masked***"
        
        if isinstance(data, dict):
            return {
                k: (mask_value if str(k).lower() in fields_to_mask else self._mask_fields(v))
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_fields(item) for item in data]

        return data
    
    def _capture_response_body(self, response) -> Optional[Dict[str, Any]]:
        """
        Handles conditional capture, truncation, and JSON parsing of the response.
        """

        resp_content = None
        
        if insider_settings.CAPTURE_RESPONSE:
            # Respect EXCLUDE_CONTENT_TYPES
            ct = response.get("Content-Type", "").lower()
            if any(excluded in ct for excluded in insider_settings.EXCLUDE_CONTENT_TYPES):
                return None
            
            # Truncate content
            content_bytes = response.content[: insider_settings.MAX_RESPONSE_LENGTH]
            
            try:
                decoded_content = content_bytes.decode(errors="replace")
                
                # Try to parse response as JSON for the Footprint model's JSONField
                if "application/json" in ct:
                    resp_content = json.loads(decoded_content)
                else:
                    resp_content = decoded_content
            
            except (UnicodeDecodeError, json.JSONDecodeError):
                resp_content = str(content_bytes) # Fallback if decoding/parsing fails
                
        return resp_content
    

    def _create_footprint_record(self, request, response, duration_ms, db_count, handler, request_id):
        """
        Collects final data, decides on execution strategy (sync/async), and saves the Footprint.
        """
        
        system_logs = handler.get_logs()
        
        request_body = self._capture_request_body(request)
        
        user_id = request.user.id if (
            insider_settings.CAPTURE_USER 
            and hasattr(request, "user") 
            and request.user.is_authenticated
        ) else None

        ip_addr = request.META.get("REMOTE_ADDR") if insider_settings.CAPTURE_IP else None
        ua = request.META.get("HTTP_USER_AGENT") if insider_settings.CAPTURE_USER_AGENT else None

        resp_content = self._capture_response_body(response)

        exception_name = getattr(request, "_insider_exception_name", None)
        stack_trace = getattr(request, "_insider_stack_trace", None)
        
        footprint_data = {
            'request_id': request_id,
            'request_user': str(user_id) if user_id else "anonymous",
            'request_path': request.path,
            'request_method': request.method.lower(),
            'request_body': request_body,
            'status_code': response.status_code,
            'response_time': duration_ms,
            'db_query_count': db_count,
            'ip_address': ip_addr,
            'user_agent': ua,
            'response_body': resp_content,
            'system_logs': system_logs,
            'exception_name': exception_name,
            'stack_trace': stack_trace,
        }
        
        db_alias_to_use = insider_settings.DB_ALIAS

        footprint_data['__db_alias'] = db_alias_to_use
        dispatch_save_footprint(footprint_data)