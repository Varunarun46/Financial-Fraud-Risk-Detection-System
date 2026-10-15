from flask import Blueprint, request, jsonify, render_template, session
from ..auth import login_required, get_current_user
from ..services.alert_service import get_alerts, update_alert_status
from ..extensions import db
from ..models import AuditLog

alert_bp = Blueprint("alerts", __name__)


@alert_bp.route("/alerts")
@login_required
def alerts_page():
    user = get_current_user()
    return render_template("alerts/alerts.html", user=user)


@alert_bp.route("/api/alerts", methods=["GET"])
@login_required
def api_get_alerts():
    """Get alerts with filtering."""
    status = request.args.get("status", "")
    severity = request.args.get("severity", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = get_alerts(status=status, severity=severity, page=page, per_page=per_page)

    return jsonify({
        "alerts": [a.to_dict() for a in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    }), 200


@alert_bp.route("/api/alerts/<alert_id>", methods=["PATCH"])
@login_required
def api_update_alert(alert_id):
    """Update alert status."""
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "Status is required"}), 400

    new_status = data["status"].upper()
    valid_statuses = ["OPEN", "REVIEWING", "RESOLVED", "DISMISSED"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    user_id = session.get("user_id")
    alert = update_alert_status(alert_id, new_status, user_id)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    # Audit log
    log = AuditLog(user_id=user_id, action="ALERT_UPDATED", details=f"Alert {alert_id} → {new_status}", ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Alert updated", "alert": alert.to_dict()}), 200
