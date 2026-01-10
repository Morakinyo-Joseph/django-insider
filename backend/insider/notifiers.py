from abc import ABC
from typing import Tuple
from .models import Footprint
from .services.slack import SlackManager


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
                f"at endpoint `{method} {endpoint}`."
            )

        elif 400 <= status_code < 500:
            header_text = f"CLIENT ERROR DETECTED: {status_code} Status Code"
            section_text = (
                f"A *Client Error ({status_code})* was made by user `{user}` to endpoint `{method} {endpoint}`. "
            )
            
        else:
            header_text = f"INFORMATIONAL: {status_code} Status Code"
            section_text = f"An event with status code {status_code} occurred for user `{user}` at `{endpoint}`."

        return header_text, section_text
    

    def _format_log_snippet(self, logs):
        """
        Helper to turn a list of log strings into a clean, truncated code block.
        """
        if not logs:
            return "No logs captured."
        
        # Join list into a single string
        if isinstance(logs, list):
            full_text = "\n".join(logs)
        else:
            full_text = str(logs)

        # Smart Truncate: Focus on the END of the logs (where the error usually is)
        if len(full_text) > 1500:
            snippet = "..." + full_text[-1500:]
        else:
            snippet = full_text

        # Wrap in Slack code block
        return f"```\n{snippet}\n```"
    

    def notify(self, footprint, context=None):
        context = context or {}
        method = footprint.request_method.upper()
        status_code = footprint.status_code
        endpoint = footprint.request_path
        user = footprint.request_user
        published_service = context.get("published_service", None)
        published_url = context.get("published_url", None)
        
        header_text, section_text = self._get_block_info(
            status_code, user, method, endpoint
        )
        
        # CLEAN THE LOGS HERE
        log_snippet = self._format_log_snippet(footprint.system_logs)

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": header_text}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"<!morakinyo> {section_text}"}},

            {"type": "divider"},

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
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*System Logs (Snippet):*\n{log_snippet}"
                }
            },

            {"type": "divider"},

            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "*Quick Reference:*"},
                    {"type": "mrkdwn", "text": f"• Response Body Snippet: `{str(footprint.response_body)[:50]}...`" },
                    # Removed "System Logs" from here because it is now in the main section above
                ]
            }
        ]

        if published_url:
            # Add the Ticket Button
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ An issue has been automatically created in *{published_service}*."
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


        payload = {
            "username": self.manager.channel,
            "blocks": blocks
        }

        self.manager.send_alert(payload)