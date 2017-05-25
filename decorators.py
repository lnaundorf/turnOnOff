from flask import request, url_for, redirect
from functools import wraps


def password_protect(password):
    def real_decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if password and request.cookies.get('password') != password:
                return redirect(url_for('login_get'))
            return func(*args, **kwargs)
        return wrapped
    return real_decorator
