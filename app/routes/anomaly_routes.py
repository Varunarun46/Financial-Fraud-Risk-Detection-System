from flask import Blueprint, request, jsonify, render_template
from ..auth import login_required, get_current_user
from ..extensions import db
from ..models import FraudPrediction
from sqlalchemy import text

anomaly_bp = Blueprint("anomaly", __name__)


@anomaly_bp.route("/anomaly-detection")
@login_required
def anomaly_page():
    user = get_current_user()
    return render_template("anomaly/anomaly.html", user=user)


@anomaly_bp.route("/api/anomalies", methods=["GET"])
@login_required
def get_anomalies():
    """Get anomalous transactions based on anomaly score."""
    try:
        rows = db.session.execute(
            text(
                "SELECT fp.transaction_id, t.amount, fp.anomaly_score, "
                "fp.risk_level, fp.prediction "
                "FROM fraud_predictions fp "
                "INNER JOIN transactions t ON fp.transaction_id = t.transaction_id "
                "WHERE fp.anomaly_score > 0.3 "
                "ORDER BY fp.anomaly_score DESC LIMIT 50"
            )
        ).fetchall()
        anomalies = []
        for r in rows:
            anomalies.append({
                "transaction_id": r[0],
                "amount": float(r[1]) if r[1] else 0,
                "anomaly_score": float(r[2]) if r[2] else 0,
                "risk_level": r[3],
                "prediction": r[4],
            })
        total = db.session.execute(text("SELECT COUNT(*) FROM fraud_predictions")).scalar()
        return jsonify({"anomalies": anomalies, "total": total}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
