from functools import wraps

# Imports
from .const import *  # noqa: F401, F403
from .crypto import aes256cbcExtended  # noqa: F401
from .cookie_manager import CookieManager  # noqa: F401
from .dt_helpers import tnow_iso, tnow_iso_str, dt_from_str, dt_from_ts, dt_to_str  # noqa: F401

# Easy inteceptor for tracing
def trace_activity(fn, trace=True):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if trace:
            print(f'TRACE: calling {fn.__name__}(), positional args: {args}, named args: {kwargs}')
        return fn(*args, **kwargs)
    return wrapper

# Error handlers
class AppError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

class DatabaseError(AppError):
    def __init__(self, error, status_code):
        super().__init__(error, status_code)

