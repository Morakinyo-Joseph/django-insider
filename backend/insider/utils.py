import sys
from typing import Any, Dict
import hashlib


try:
    from django.conf import settings as django_settings
except ImportError:
    django_settings = None


def is_celery_available() -> bool:
    """
    Checks if Celery is installed AND sufficiently configured in Django settings 
    to be used for background tasks.
    """
    
    try:
        import celery
    except ImportError:
        return False
    
    if not django_settings:
        return False

    if hasattr(django_settings, 'CELERY_BROKER_URL') and django_settings.CELERY_BROKER_URL:
        return True
    
    if hasattr(django_settings, 'BROKER_URL') and django_settings.BROKER_URL:
        return True
    
    if hasattr(django_settings, 'CELERY') and isinstance(django_settings.CELERY, dict):
        celery_config: Dict[str, Any] = django_settings.CELERY
        
        if celery_config.get('broker_url') or celery_config.get('BROKER_URL'):
            return True
            
    return False


def generate_fingerprint(footprint_data: dict) -> str:
    """
    Generates a unique MD5 hash to group errors.
    """

    stack_trace = footprint_data.get("stack_trace")
    exc_name = footprint_data.get("exception_name")
    path = footprint_data.get("request_path", '')
    status = footprint_data.get("status_code", 200)

    identify_string = ""

    if stack_trace and isinstance(stack_trace, list) and len(stack_trace) > 0:
        # The last frame of the stack trace is where the crash actually happened.
        last_frame = stack_trace[-1]
        file_name = last_frame.get('file', 'unknown')
        line_no = last_frame.get('line', 0) 

        # Identify = "ValueError|views.py|42"
        identify_string = f"{exc_name}|{file_name}|{line_no}"

    else:
        # NOTE: Normalize paths (e.g. replace IDs with {id})
        # to prevent /user2/1 and /users/2 creating different incidences
        identify_string = f"{status}|{path}"

    return hashlib.md5(identify_string.encode('utf-8')).hexdigest()
