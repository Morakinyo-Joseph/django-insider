from insider.settings import settings as insider_settings

class InsiderRouter:
    """
    A router to control all database operations for models in the 'insider' 
    application (where Insider resides), directing them to the configured DB_ALIAS.
    """

    route_app_labels = {'insider'}

    INSIDER_DB_ALIAS = insider_settings.DB_ALIAS
    
    def db_for_read(self, model, **hints):
        """
        Attempts to read models in the router's app_labels go to the configured database.
        """

        if model._meta.app_label in self.route_app_labels:
            return self.INSIDER_DB_ALIAS
        return None 
    
    def db_for_write(self, model, **hints):
        """
        Attempts to write models in the router's app_labels go to the configured database.
        """

        if model._meta.app_label in self.route_app_labels:
            return self.INSIDER_DB_ALIAS
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations only if both objects are on the same database.
        If both are Insider models, they're on the Insider DB.
        If neither are Insider models, they're on 'default' (or another router's choice).
        """
        
        app1 = obj1._meta.app_label
        app2 = obj2._meta.app_label
        
        if app1 in self.route_app_labels and app2 in self.route_app_labels:
            return True

        if app1 in self.route_app_labels or app2 in self.route_app_labels:
            return False 
            
        return None 
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure migrations for models in route_app_labels only run on the configured database.
        And all other app migrations do NOT run on the configured database.
        """
        
        if app_label in self.route_app_labels:
            return db == self.INSIDER_DB_ALIAS
            
        elif db == self.INSIDER_DB_ALIAS:
            return False 
            
        return None