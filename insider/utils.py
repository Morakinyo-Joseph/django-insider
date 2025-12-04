import sys
from typing import Any

try:
    from django.conf import settings as django_settings
except ImportError:
    django_settings = None


def is_celery_available() -> bool:
    """
    Checks if Celery is installed AND sufficiently configured in Django settings 
    to be used for background tasks.
    """
    
    try:
        import celery
    except ImportError:
        return False
    
    if not django_settings:
        return False

    if hasattr(django_settings, 'CELERY_BROKER_URL') and django_settings.CELERY_BROKER_URL:
        return True
    
    if hasattr(django_settings, 'BROKER_URL') and django_settings.BROKER_URL:
        return True
    
    if hasattr(django_settings, 'CELERY') and isinstance(django_settings.CELERY, dict):
        celery_config: dict[str, Any] = django_settings.CELERY
        
        if celery_config.get('broker_url') or celery_config.get('BROKER_URL'):
            return True
            
    return False