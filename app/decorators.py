from functools import wraps
from flask import abort
from flask_login import current_user

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    #wow, this is crazy smart (the first part of the function)
    #is executed and depending on the outcome, the return value is
    #the decorated_function and decorator
    return permission_required(Permission.ADMINISTRATOR)(f)
