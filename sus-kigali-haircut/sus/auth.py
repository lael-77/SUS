"""Authentication helpers — role-based access control (documentation Section 4.1).

Roles:
    super_admin : full access (owner)
    manager     : day-to-day operations (no settings / payroll)
    worker      : sees only own schedule, own clients, own earnings

The login/logout routes themselves live in the admin blueprint.
"""
from functools import wraps

from flask import session, redirect, url_for, request

from .models import User


def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("admin.login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            u = current_user()
            if not u:
                return redirect(url_for("admin.login", next=request.path))
            if u.role not in roles:
                return "Forbidden — you do not have permission to view this page.", 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

