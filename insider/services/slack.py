import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SlackManager:
    """
    Handles slack alerts.
    """
    
    def __init__(self):
        self.webhook = settings.SLACK_WEBHOOK_URL
        self.channel = settings.SLACK_CHANNEL_NAME

    def send_alert(self, payload):
        try:
            response = requests.post(
                url=self.webhook,
                json=payload,
                timeout=5
            )
            response.raise_for_status()

        except (requests.HTTPError, ConnectionError, requests.Timeout) as e:
            logger.warning(f"INSIDER: Failed to send Slack message (attempt {self.request.retries + 1}): {e}. Retrying...")
            raise self.retry(exc=e)
        
        except Exception as e:
            logger.info(f"INSIDER: Error sending slack message: {e}")
            raise