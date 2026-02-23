import requests
import logging
from typing import Tuple
from .base import BaseIntegration

logger = logging.getLogger(__name__)

class SlackIntegration(BaseIntegration):
    identifier = "slack"
    logo_url = "https://upload.wikimedia.org/wikipedia/commons/d/d5/Slack_icon_2019.svg"
    
    config_definition = {
        "webhook_url": {
            "label": "Slack Webhook URL",
            "type": "PASSWORD",
            "required": True,
            "help_text": "Incoming Webhook URL from your Slack App."
        },
        "channel": {
            "label": "Channel Name (Optional)",
            "type": "STRING",
            "required": False,
            "default": "#general",
            "help_text": "Override the default channel (e.g. #alerts)"
        }
    }

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
        if not logs:
            return "No logs captured."
        
        full_text = "\n".join(logs) if isinstance(logs, list) else str(logs)

        # Smart Truncate: Focus on the END of the logs
        if len(full_text) > 1500:
            snippet = "..." + full_text[-1500:]
        else:
            snippet = full_text

        return f"```\n{snippet}\n```"

    def run(self, footprint, context):
        webhook = self.get_config("webhook_url")
        channel = self.get_config("channel")
        if not webhook:
            return

        context = context or {}
        method = footprint.request_method.upper()
        status_code = footprint.status_code
        endpoint = footprint.request_path
        user = footprint.request_user
        
        # previous integration dropped data in the bucket
        issues = context.get("generated_issues", [])
        
        if not issues and context.get("issue_url"):
             issues = [{
                 "system": context.get("issue_system"),
                 "url": context.get("issue_url"),
                 "key": context.get("issue_key")
             }]

        header_text, section_text = self._get_block_info(status_code, user, method, endpoint)
        log_snippet = self._format_log_snippet(footprint.system_logs)

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": header_text}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"<!morakinyo> {section_text}"}}, # TODO: Who to alert on slack could be dynamic.
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
                ]
            }
        ]

        if issues:
            button_elements = []
            for issue in issues:
                sys = issue.get("system", "External")
                url = issue.get("url")
                key = issue.get("key", "Link")

                if url:
                    button_elements.append({
                        "type": "button",
                        "text": {
                            "type": "plain_text", 
                            "text": f"View on {sys} ({key})",
                            "emoji": True
                        },
                        "url": url,
                        "action_id": f"view_{sys.lower()}_{key}"
                    })

            if button_elements:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Issues Created:*"
                    }
                })
                blocks.append({
                    "type": "actions",
                    "elements": button_elements[:5] # Limit to 5 buttons
                })

        payload = {"blocks": blocks}
        if channel:
            payload["username"] = channel

        # 6. Send
        try:
            requests.post(webhook, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"INSIDER: Slack send failed: {e}")