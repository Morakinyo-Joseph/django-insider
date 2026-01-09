import time
import logging

LOG = logging.getLogger(__name__)

def execution_time(func):
    """
    A decorator that measures the time is takes to execute a function.
    Time result is displayed in milliseconds (ms).
    """
    
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result= func(*args, **kwargs)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        LOG.info(f"Total Execution time: {total_time}")
        return result
    
    return wrapper