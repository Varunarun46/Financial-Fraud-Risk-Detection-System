"""Alert service — automatic fraud alert generation."""
import uuid
from datetime import datetime
from ..extensions import db
from ..models import FraudAlert, Transaction
from .risk_engine import calculate_risk_score, get_risk_level, get_risk_factors


def create_alert(transaction_id, fraud_probability, risk_score, risk_level, amount=None, transaction_type=None, **kwargs):
    """Create a fraud alert if risk exceeds threshold."""
    if risk_level not in ["HIGH", "CRITICAL"]:
        return None

    severity = "CRITICAL" if risk_level == "CRITICAL" else "HIGH"
    factors = get_risk_factors(
        amount=amount,
        transaction_type=transaction_type,
        old_balance=kwargs.get("old_balance"),
        new_balance=kwargs.get("new_balance"),
        fraud_probability=fraud_probability,
    )

    alert = FraudAlert(
        alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        transaction_id=transaction_id,
        severity=severity,
        title=f"{severity} Risk: Transaction {transaction_id}",
        message="; ".join(factors) if factors else "Unusual transaction behavior detected.",
        status="OPEN",
    )
    db.session.add(alert)
    db.session.commit()
    return alert


def get_alerts(status=None, severity=None, page=1, per_page=20):
    """Get alerts with optional filtering."""
    query = FraudAlert.query
    if status:
        query = query.filter(FraudAlert.status == status.upper())
    if severity:
        query = query.filter(FraudAlert.severity == severity.upper())
    return query.order_by(FraudAlert.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)


def update_alert_status(alert_id, new_status, user_id=None):
    """Update alert status."""
    alert = FraudAlert.query.filter_by(alert_id=alert_id).first()
    if not alert:
        return None
    alert.status = new_status
    if user_id:
        alert.assigned_to = user_id
    db.session.commit()
    return alert
