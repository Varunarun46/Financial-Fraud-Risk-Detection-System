from flask import Blueprint, render_template, redirect, url_for, session
from ..auth import login_required, get_current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    if user.is_admin():
        return redirect(url_for("admin.admin_panel"))
    return render_template("dashboard/dashboard.html", user=user)
