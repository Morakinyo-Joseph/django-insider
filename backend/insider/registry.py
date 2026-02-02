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
        db_integrations = InsiderIntegration.objects.filter(is_active=True)\
            .prefetch_related('config_keys')\
            .order_by('order')

        for db_obj in db_integrations:
            integration_class = INTEGRATION_REGISTRY.get(db_obj.identifier)

            if integration_class:
                try:
                    instance = integration_class(db_instance=db_obj)
                    active_instances.append(instance)
                except Exception as e:
                    logger.error(f"INSIDER: Failed to initialize integration '{db_obj.name}': {e}")
            else:
                logger.warning(f"INSIDER: Integration '{db_obj.identifier}' found in DB but code is missing in REGISTRY.")
                
    except Exception as e:
        logger.error(f"INSIDER: Error fetching active integrations: {e}")

    return active_instances