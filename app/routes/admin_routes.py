from flask import Blueprint, request, jsonify, render_template, session
from ..auth import login_required, get_current_user
from ..extensions import db
from ..models import User, AuditLog, SystemSetting

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@login_required
def admin_panel():
    user = get_current_user()
    return render_template("admin/admin_dashboard.html", user=user)


@admin_bp.route("/admin/users")
@login_required
def users_page():
    user = get_current_user()
    return render_template("admin/users.html", user=user)


@admin_bp.route("/admin/audit-logs")
@login_required
def audit_logs_page():
    user = get_current_user()
    return render_template("admin/audit_logs.html", user=user)


@admin_bp.route("/admin/settings")
@login_required
def settings_page():
    user = get_current_user()
    return render_template("admin/settings.html", user=user)


# --- API Endpoints ---

@admin_bp.route("/api/users", methods=["GET"])
@login_required
def get_users():
    users = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


@admin_bp.route("/api/users/<int:user_id>", methods=["PATCH"])
@login_required
def update_user(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if "role" in data:
        user.role = data["role"].upper()
    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()

    # Audit log
    admin_id = session.get("user_id")
    log = AuditLog(user_id=admin_id, action="USER_ROLE_CHANGED", details=f"User {user.username} role changed to {user.role}", ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "User updated", "user": user.to_dict()}), 200


@admin_bp.route("/api/audit-logs", methods=["GET"])
@login_required
def get_audit_logs():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "logs": [l.to_dict() for l in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200


@admin_bp.route("/api/settings", methods=["GET"])
@login_required
def get_settings():
    settings = SystemSetting.query.all()
    return jsonify({"settings": [s.to_dict() for s in settings]}), 200


@admin_bp.route("/api/settings/<key>", methods=["PUT"])
@login_required
def update_setting(key):
    data = request.get_json()
    setting = SystemSetting.query.filter_by(key=key).first()
    if not setting:
        setting = SystemSetting(key=key, value=str(data.get("value", "")), description=data.get("description", ""))
        db.session.add(setting)
    else:
        setting.value = str(data.get("value", setting.value))
        if "description" in data:
            setting.description = data["description"]
    db.session.commit()

    # Audit log
    admin_id = session.get("user_id")
    log = AuditLog(user_id=admin_id, action="SETTINGS_CHANGED", details=f"Setting '{key}' updated to '{setting.value}'", ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Setting updated", "setting": setting.to_dict()}), 200
