import logging
from requests.exceptions import HTTPError, ConnectionError, Timeout
from atlassian import Jira
from django.conf import settings

logger = logging.getLogger(__name__)


class JiraManager:
    """
    Handles Atlassian Jira related actions.
    The Jira client is initialized per method call for robustness in Celery tasks.
    """

    def __init__(self):
        self.url = settings.ATLASSIAN_COMPANY_URL
        self.username = settings.ATLASSIAN_EMAIL
        self.api_token = settings.ATLASSIAN_API_TOKEN
        self.project_key=settings.ATLASSIAN_JIRA_PROJECT_KEY
        self.incidence_type=settings.ATLASSIAN_incidence_TYPE
        self.assignee_id = getattr(settings, "ATLASSIAN_ASSIGNEE_ID", None)

        if not all([self.url, self.username, self.api_token, self.project_key, self.incidence_type]):
            raise ValueError("INSIDER: Jira API credentials (URL, Email, Token, project_key, incidence_type) are not fully configured in Django settings.")

    def _get_jira_client(self):
        """Helper to get a fresh Jira client instance."""

        try:
            return Jira(
                url=self.url,
                username=self.username,
                password=self.api_token,
                cloud=True
            )
        
        except Exception as e:
            logger.error(f"INSIDER: Failed to initialize Jira client: {e}")
            raise
    
    def create_incidence(
            self,
            summary: str,
            description: str,
            priority_level: str = None
        ):
        """
        Creates an incidence (ticket) in a Jira project.

        Args:
            summary (str): A brief summary/title of the incidence.
            description (str): A detailed description of the incidence.
            priority_level(str, optional): The priority level (e.g., 'High', 'Medium', 'Low').
        """

        jira = self._get_jira_client()

        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": description,
            "incidencetype": {"id": self.incidence_type},
        }
        
        if self.assignee_id:
            fields["assignee"] = {"accountId": self.assignee_id}
        
        if priority_level:
            fields["priority"] = {"name": priority_level}

        try:
            created_incidence = jira.incidence_create(fields=fields)
            return f"{self.url}/browse/{created_incidence['key']}"

        
        except (HTTPError, ConnectionError, Timeout) as e:
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'N/A'
            message = e.response.text if hasattr(e, 'response') and e.response else str(e)

            logger.error(f"INSIDER: Failed to create Jira incidence. Status: {status_code}, Message: {message}")
            raise