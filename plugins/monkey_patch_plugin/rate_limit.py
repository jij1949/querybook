import functools
import time
from lib.logger import get_logger

LOG = get_logger(__file__)


def rate_limit(_func=None, *, min_interval=0):
    """
    Reusable decorator to rate limit a function. Can either be called with a function,
    or added as a decorator.

    Examples:

    ```
    @rate_limit(min_interval=10)
    def my_func():
        pass
    ```

    ```
    rate_limited_func = rate_limit(my_func, min_interval=10)
    ```

    @param min_interval: minimum interval between calls in seconds
    """

    def decorator(func):
        last_called = [0.0]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                LOG.debug(
                    f"Rate limiting {func.__name__}. Waiting {left_to_wait} seconds"
                )
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret

        return wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)
