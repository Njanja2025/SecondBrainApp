import time
import functools

def retry_on_exception(max_retries=3, delay=1, exceptions=(Exception,)):
    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator_retry
