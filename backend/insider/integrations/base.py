import logging
from typing import Dict, Any, List
logger = logging.getLogger(__name__)

class BaseIntegration:
    """
    Base class for all integrations. 
    Configurations are fetched from the DB, not settings.py.
    """

    identifier = None 
    
    config_definition = {}

    def __init__(self, db_instance=None):
        self.db_instance = db_instance
        self._config_cache = {}
        
        # If initialized with a DB instance, load config immediately
        if db_instance:
            self._load_config_from_instance(db_instance)

    def _load_config_from_instance(self, instance):
        """
        Loads keys from the pre-fetched database instance.
        """
        for config in instance.config_keys.all():
            self._config_cache[config.key] = config.value

    def get_config(self, key=None, default=None):
        """
        Helper to retrieve a config value.
        """
        if key is None:
            return self._config_cache
        return self._config_cache.get(key, default)

    def run(self, footprint, context):
        """
        The main logic.
        Args:
            footprint: The error data dictionary.
            context: The Shared Context dictionary (Waterfall).
        Returns:
            dict (optional): Data to update the context with.
        """
        raise NotImplementedError("Subclasses must implement run()")
    
    def create_issue_payload(
            self, 
            context: Dict[str, Any], 
            system: str, 
            url: str, 
            key: str
        ) -> Dict[str, Any]:
  
        current_issues = context.get("generated_issues", [])
        if not isinstance(current_issues, list):
            current_issues = []
        
        new_issue = {
            "system": system,
            "url": url,
            "key": key
        }
        
        logger.info(f"INSIDER: Created {system} Issue: {url}")

        return {
            "generated_issues": current_issues + [new_issue],
            "issue_system": system,
            "issue_url": url,
            "issue_key": key
        }