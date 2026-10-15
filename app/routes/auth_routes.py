import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from ..extensions import db
from ..models import User, AuditLog
from ..auth import login_required, get_current_user

auth_bp = Blueprint("auth", __name__)


def log_action(user_id, action, details=None):
    log = AuditLog(user_id=user_id, action=action, details=details, ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()


def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one digit."
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account has been deactivated. Contact an administrator.", "danger")
                return render_template("auth/login.html")

            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            session["full_name"] = user.full_name
            user.last_login = datetime.now()
            db.session.commit()
            log_action(user.id, "LOGIN", f"User {user.username} logged in successfully")
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "VIEWER").upper()

        # Validation
        if not all([full_name, username, email, password]):
            flash("All required fields must be filled.", "danger")
            return render_template("auth/register.html")

        if role not in ("VIEWER", "ANALYST", "ADMIN"):
            flash("Invalid role selected.", "danger")
            return render_template("auth/register.html")

        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", username):
            flash("Username must be 3-30 characters (letters, numbers, underscores only).", "danger")
            return render_template("auth/register.html")

        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            flash("Please enter a valid email address.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        pwd_error = validate_password(password)
        if pwd_error:
            flash(pwd_error, "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("auth/register.html")

        user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            role=role,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        log_action(user.id, "REGISTER", f"New user registered: {username} ({email})")
        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    user = get_current_user()
    if user:
        log_action(user.id, "LOGOUT")
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# --- API Auth Endpoints ---

@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({"error": "Account deactivated"}), 403
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        session["full_name"] = user.full_name
        user.last_login = datetime.now()
        db.session.commit()
        log_action(user.id, "LOGIN", f"User {user.username} logged in successfully")
        return jsonify({"message": "Login successful", "user": user.to_dict()}), 200

    return jsonify({"error": "Invalid username or password"}), 401


@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    role = data.get("role", "VIEWER").upper()

    if not all([full_name, username, email, password]):
        return jsonify({"error": "All required fields must be filled"}), 400

    if role not in ("VIEWER", "ANALYST", "ADMIN"):
        return jsonify({"error": "Invalid role"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    pwd_error = validate_password(password)
    if pwd_error:
        return jsonify({"error": pwd_error}), 400

    user = User(full_name=full_name, username=username, email=email, phone=phone, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    log_action(user.id, "REGISTER", f"New user registered: {username} ({email})")
    return jsonify({"message": "Registration successful", "user": user.to_dict()}), 201


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def api_logout():
    user = get_current_user()
    if user:
        log_action(user.id, "LOGOUT", f"User {user.username} logged out")
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200
