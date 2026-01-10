from abc import ABC
import uuid
import json
from .models import Footprint
from .services.jira import JiraManager

class BasePublisher(ABC):
    """ Generic contract for all publishing services. """
    
    def publish(self, footprint: Footprint, context=None):
        raise NotImplementedError



class JiraPublisher(BasePublisher):
    def __init__(self):
        self.manager = JiraManager()

    def _format_logs(self, logs):
        """Helper to join list of logs into a clean string with newlines."""
        
        if not logs:
            return "N/A"
        
        if isinstance(logs, list):
            return "\n".join(logs)
        
        return str(logs)
    
    def _format_json(self, body):
        """Helper to pretty-print JSON response body."""

        if not body:
            return "N/A"
        
        try:
            if isinstance(body, str):
                parsed = json.loads(body)
                return json.dumps(parsed, indent=4)
            
            return json.dumps(body, indent=4)
        
        except Exception:
            return str(body)
        


    def publish(self, footprint, context=None):
        """
        Returns jira ticket url.
        """

        context = context or {}
        summary = context.get("title", f"Insider Error: {footprint.status_code} at {footprint.request_path}")
        
        logs_text = self._format_logs(footprint.system_logs)
        response_text = self._format_json(footprint.response_body)
        request_text = self._format_json(footprint.request_body)

        description = (
            f"h2. Error Details\n"
            f"||Key||Value||\n"
            f"|*Footprint ID*|{footprint.id}|\n"
            f"|*User*|{footprint.request_user}|\n"
            f"|*Endpoint*|{footprint.request_method.upper()} {footprint.request_path}|\n"
            f"|*Status*|{footprint.status_code}|\n"
            f"|*Response Time*|{footprint.response_time:.2f} ms|\n"
            f"|*Occurred At*|{footprint.created_at.isoformat()}|\n\n"

            f"h2. Request Body\n"
            f"{{code:json}}\n"
            f"{request_text}\n"
            f"{{code}}\n\n"

            f"h2. Response Body\n"
            f"{{code:json}}\n"
            f"{response_text}\n"
            f"{{code}}\n\n"

            f"h2. System Logs\n"
            f"{{noformat}}\n"
            f"{logs_text}\n"
            f"{{noformat}}\n\n"
        )
        
        issue = self.manager.create_issue(
            summary=summary,
            description=description,
            priority_level="Highest" if footprint.status_code >= 500 else "Medium"
        )

        return {
            "published_url": issue,
            "published_service": "Jira",
            "external_id": str(issue).strip("/")[-1]
        }
