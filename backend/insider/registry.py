import logging
from insider.models import InsiderIntegration
from insider.integrations.slack import SlackIntegration
from insider.integrations.jira import JiraIntegration
from insider.integrations.github import GithubIntegration
from insider.integrations.gmail import GmailIntegration


logger = logging.getLogger(__name__)


INTEGRATION_REGISTRY = {
    "slack": SlackIntegration,
    "jira": JiraIntegration, 
    "github": GithubIntegration,
    "gmail": GmailIntegration
}

def get_active_integrations():
    """
    Fetches active integrations from the DB, sorts them by user-defined Order,
    and initializes the Python classes with the DB config.
    """
    active_instances = []

    try:
        return InsiderIntegration.objects.filter(is_active=True)\
            .prefetch_related('config_keys')\
            .order_by('order')
                
    except Exception as e:
        logger.error(f"INSIDER: Error fetching active integrations: {e}")

    return active_instances