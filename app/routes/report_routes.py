import csv
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, Response
from ..auth import login_required, get_current_user
from ..extensions import db
from ..models import Transaction, FraudPrediction, FraudAlert, ModelResult, AuditLog

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports")
@login_required
def reports_page():
    user = get_current_user()
    return render_template("reports/reports.html", user=user)


@report_bp.route("/api/reports/fraud", methods=["GET"])
@login_required
def fraud_report():
    """Generate fraud detection report."""
    fraud_tx = Transaction.query.filter_by(is_fraud=True).all()
    total_tx = Transaction.query.count()
    fraud_count = len(fraud_tx)
    fraud_rate = (fraud_count / total_tx * 100) if total_tx > 0 else 0

    total_amount = db.session.query(db.func.sum(Transaction.amount)).scalar() or 0
    fraud_amount = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.is_fraud == True).scalar() or 0

    return jsonify({
        "report_type": "fraud_detection",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_transactions": total_tx,
            "fraud_transactions": fraud_count,
            "fraud_rate": round(fraud_rate, 4),
            "total_amount": float(total_amount),
            "fraud_amount": float(fraud_amount),
        },
        "fraud_transactions": [t.to_dict() for t in fraud_tx[:100]],
    }), 200


@report_bp.route("/api/reports/model-performance", methods=["GET"])
@login_required
def model_performance_report():
    """Generate model performance report."""
    results = ModelResult.query.order_by(ModelResult.created_at.desc()).all()
    return jsonify({
        "report_type": "model_performance",
        "generated_at": datetime.now().isoformat(),
        "models": [r.to_dict() for r in results],
    }), 200


@report_bp.route("/api/reports/risk", methods=["GET"])
@login_required
def risk_report():
    """Generate risk analysis report."""
    predictions = FraudPrediction.query.all()
    risk_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for p in predictions:
        level = p.risk_level or "LOW"
        risk_levels[level] = risk_levels.get(level, 0) + 1

    return jsonify({
        "report_type": "risk_analysis",
        "generated_at": datetime.now().isoformat(),
        "risk_distribution": risk_levels,
        "total_predictions": len(predictions),
    }), 200


@report_bp.route("/api/reports/alerts", methods=["GET"])
@login_required
def alerts_report():
    """Generate alert summary report."""
    alerts = FraudAlert.query.all()
    status_counts = {"OPEN": 0, "REVIEWING": 0, "RESOLVED": 0, "DISMISSED": 0}
    severity_counts = {"HIGH": 0, "CRITICAL": 0, "MEDIUM": 0, "LOW": 0}
    for a in alerts:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1
        severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1

    return jsonify({
        "report_type": "alert_summary",
        "generated_at": datetime.now().isoformat(),
        "status_distribution": status_counts,
        "severity_distribution": severity_counts,
        "total_alerts": len(alerts),
        "alerts": [a.to_dict() for a in alerts[:50]],
    }), 200


@report_bp.route("/api/reports/export/<format>", methods=["GET"])
@login_required
def export_report(format):
    """Export report as CSV."""
    if format != "csv":
        return jsonify({"error": "Only CSV export is supported"}), 400

    # Export transactions with predictions
    transactions = Transaction.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Transaction ID", "Dataset", "Type", "Amount", "Fraud", "Risk Level", "Prediction", "Date"])

    for tx in transactions:
        pred = FraudPrediction.query.filter_by(transaction_id=tx.transaction_id).first()
        writer.writerow([
            tx.transaction_id,
            tx.dataset_name,
            tx.transaction_type,
            float(tx.amount) if tx.amount else 0,
            "Yes" if tx.is_fraud else "No",
            pred.risk_level if pred else "",
            pred.prediction if pred else "",
            tx.transaction_timestamp.isoformat() if tx.transaction_timestamp else "",
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=fraud_report_{datetime.now().strftime('%Y%m%d')}.csv"},
    )
