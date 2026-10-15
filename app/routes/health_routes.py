from flask import Blueprint, jsonify, current_app
from sqlalchemy import text

from ..extensions import db

health_bp = Blueprint('health_bp', __name__)


@health_bp.route('/')
@health_bp.route('/health')
def health_check():
    try:
        db.session.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        database_status = "disconnected"

    return jsonify({
        "status": "ok",
        "phase": 1,
        "database": database_status,
        "message": "Financial Fraud Risk System API is running"
    }), 200