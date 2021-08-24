from functools import wraps

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
        super.__init__(self, error, status_code)

