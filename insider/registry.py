import logging
from insider.settings import settings as insider_settings 
from .publishers import JiraPublisher
from .notifiers import SlackNotifier

logger = logging.getLogger(__name__)


PUBLISHER_REGISTRY = {
    "jira": JiraPublisher,
}


NOTIFIER_REGISTRY = {
    "slack": SlackNotifier,
}


def get_active_publishers():
    """
    Reads INSIDER_PUBLISHERS from settings and looks them up in the registry.

    Returns:
        INITIALIZED objects (e.g., [JiraPublisher()])
    """
    
    config_keys = insider_settings.PUBLISHERS

    active_instances = []

    for key in config_keys:
        lookup_key = str(key).lower()       
        publisher_class = PUBLISHER_REGISTRY.get(lookup_key)

        if publisher_class:
            try:
                instance = publisher_class() # initialize the class
                active_instances.append(instance)
            except Exception as e:
                logger.error(f"INSIDER: Failed to initialize Publisher '{key}': {e}")
        else:
            logger.warning(f"INSIDER: Publisher '{key}' is in settings but NOT in registry.")
    
    return active_instances



def get_active_notifiers():
    """
    Reads INSIDER_NOTIFIERS from settings and looks them up in the registry.
    
    Returns:
        INITIALIZED objects (e.g., [SlackNotifier()])
    """
    
    config_keys = insider_settings.NOTIFIERS

    active_instances = []

    for key in config_keys:
        lookup_key = str(key).lower()
        notifier_class = NOTIFIER_REGISTRY.get(lookup_key)

        if notifier_class:
            try:
                instance = notifier_class() # initialize the class
                active_instances.append(instance)
            except Exception as e:
                logger.error(f"INSIDER: Failed to initialize Notifier '{key}': {e}")
        else:
            logger.warning(f"INSIDER: Notifier '{key}' is in settings but NOT in registry.")
    
    return active_instances



    