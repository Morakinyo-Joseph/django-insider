from threading import Thread
from insider.services.footprint import save_footprint
from insider.utils import is_celery_available


def dispatch_save_footprint(footprint_data: dict):
    """
    Makes use of celery to save, otherwise defaults to thread.
    """

    if is_celery_available():
        try:
            from insider.tasks import save_footprint_task
            save_footprint_task.delay(footprint_data)
            return
        except Exception:
            pass

    # Fallback to no celery configuration
    Thread(
        target=save_footprint,
        args=(footprint_data,),
        daemon=True,
    ).start()
