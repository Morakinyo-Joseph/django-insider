from abc import ABC
from typing import Tuple
from .models import Footprint
from modules.slack import SlackManager


class BaseNotifier(ABC):
    """ Generic contract for all notifier services. """

    def notify(self, footprint: Footprint, context=None):
        raise NotImplementedError
    


class SlackNotifier(BaseNotifier):
    def __init__(self):
        self.manager = SlackManager()

    def _get_block_info(self, status_code, user, method, endpoint) -> Tuple[str, str]:
        if status_code >= 500:
            header_text = f"SERVER ERROR ALERT: {status_code} Internal Server Error"
            section_text = (
                f"An *Internal Server Error ({status_code})* has occurred for user `{user}` "
                f"at endpoint `{method} {endpoint}`. This indicates a server-side issue that requires investigation."
            )

        elif 400 <= status_code < 500:
            header_text = f"CLIENT ERROR DETECTED: {status_code} Status Code"
            section_text = (
                f"A *Client Error ({status_code})* was made by user `{user}` to endpoint `{method} {endpoint}`. "
                f"This typically indicates an issue with the client's request (e.g., malformed data, missing parameters) "
                f"or an authorization problem."
            )
            
        else:
            header_text = f"INFORMATIONAL: {status_code} Status Code"
            section_text = f"An event with status code {status_code} occurred for user `{user}` at `{endpoint}`."

        return header_text, section_text
    

    def notify(self, footprint, context=None):
        method = footprint.request_method.upper()
        status_code = footprint.status_code
        endpoint = footprint.request_path
        user = footprint.request_user
        published_service = context.get("published_service", None)
        published_url = context.get("published_url", None)
        
        header_text, section_text = self._get_block_info(
            status_code, user, method, endpoint
        )

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": header_text,}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"<!channel> {section_text}"} },

            {"type": "divider" },

            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Endpoint:*\n`{method} {endpoint}`"},
                    {"type": "mrkdwn", "text": f"*Status Code:*\n`{status_code}`"},
                    {"type": "mrkdwn", "text": f"*Affected User:*\n`{user}`"},
                    {"type": "mrkdwn", "text": f"*Response Time:*\n`{footprint.response_time:.2f} ms`"},
                    {"type": "mrkdwn", "text": f"*Occurred At (UTC):*\n`{footprint.created_at}`"}
                ]
            },

            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "*Quick Reference:*"},
                    {"type": "mrkdwn", "text": f"• Response Body Snippet: `{str(footprint.response_body)[:50]}...`"  },
                    {"type": "mrkdwn", "text": f"• System Logs Snippet: `{footprint.system_logs[:50]}...`" }
                ]
            }
        ]


        if published_url:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"A issue has been automatically created in {published_service} to track this event. "
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": f"View on {published_service}"
                    },
                    "url": published_url,
                    "action_id": "view_external_issue"
                },  
            })
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"• Full details: <{published_url}|Click here>"}
                ]
            })


        payload = {
            "username": self.manager.channel,
            "blocks": blocks
        }

        self.manager.send_alert(payload)