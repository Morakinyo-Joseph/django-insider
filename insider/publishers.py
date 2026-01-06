from abc import ABC
import uuid
from .models import Footprint
from modules.jira import JiraManager


class BasePublisher(ABC):
    """ Generic contract for all publishing services. """
    
    def publish(self, footprint: Footprint, context=None):
        raise NotImplementedError



class JiraPublisher(BasePublisher):
    def __init__(self):
        self.manager = JiraManager()

    def publish(self, footprint, context=None):
        """
        Returns jira ticket url.
        """

        # TODO: replace short_uuid with a hashed fingerprint
        
        short_uuid = str(uuid.uuid4())[:5]
        summary = f"Insider Error: {footprint.status_code} User Error at {footprint.request_path} {short_uuid}"
        description = (
            f"*Footprint ID:* {footprint.id}\n"
            f"*User ID:* {footprint.request_user}\n"
            f"*Endpoint:* {footprint.request_path}\n"
            f"*Method:* {footprint.request_method.upper()}\n"
            f"*Status Code:* {footprint.status_code}\n"
            f"*Response Time:* {footprint.response_time:.2f} ms\n"
            f"*Created At:* {footprint.created_at.isoformat()}\n\n"

            f"--- *Response Body* ---\n"
            f"{{code:json}}\n{footprint.response_body if footprint.response_body else 'N/A'}\n{{code}}\n\n"

            f"--- *System Logs* ---\n"
            f"{{noformat}}\n{footprint.system_logs if footprint.system_logs else 'N/A'}\n{{noformat}}"
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
