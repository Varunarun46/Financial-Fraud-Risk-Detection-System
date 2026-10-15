from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from .models import User


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Authentication required"}), 401
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.is_json:
                    return jsonify({"error": "Authentication required"}), 401
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            user = User.query.get(session["user_id"])
            if not user or not user.is_active:
                session.clear()
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("auth.login"))
            if roles and user.role not in roles:
                if request.is_json:
                    return jsonify({"error": "Insufficient permissions"}), 403
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("main.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required("ADMIN")(f)


def analyst_required(f):
    return role_required("ADMIN", "ANALYST")(f)


def get_current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None
