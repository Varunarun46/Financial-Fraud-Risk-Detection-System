"""Risk scoring engine — combines ML probability, anomaly score, and business rules."""
import os
import json
from ..extensions import db
from ..models import SystemSetting


def get_thresholds():
    """Get risk thresholds from system settings."""
    defaults = {"low": 30, "medium": 60, "high": 80}
    settings = SystemSetting.query.filter(SystemSetting.key.like("risk_threshold_%")).all()
    for s in settings:
        try:
            level = s.key.replace("risk_threshold_", "")
            defaults[level] = int(s.value)
        except (ValueError, KeyError):
            pass
    return defaults


def calculate_risk_score(fraud_probability, anomaly_score=0, amount=None, transaction_type=None):
    """
    Calculate final risk score (0-100) combining:
    - ML fraud probability (weight: 0.6)
    - Anomaly score (weight: 0.2)
    - Business rules (weight: 0.2)
    """
    # ML component (60%)
    ml_score = (fraud_probability or 0) * 100 * 0.6

    # Anomaly component (20%)
    anomaly_component = (anomaly_score or 0) * 100 * 0.2

    # Business rules component (20%)
    business_score = 0
    if amount:
        if amount > 50000:
            business_score += 40
        elif amount > 10000:
            business_score += 20
        elif amount > 5000:
            business_score += 10
    if transaction_type:
        high_risk_types = ["TRANSFER", "CASH_OUT"]
        if transaction_type.upper() in high_risk_types:
            business_score += 30
    business_score = min(business_score, 100) * 0.2

    final_score = round(ml_score + anomaly_component + business_score, 2)
    return min(max(final_score, 0), 100)


def get_risk_level(score):
    """Categorize risk score into levels."""
    thresholds = get_thresholds()
    if score >= thresholds["high"]:
        return "CRITICAL"
    elif score >= thresholds["medium"]:
        return "HIGH"
    elif score >= thresholds["low"]:
        return "MEDIUM"
    return "LOW"


def get_risk_factors(amount=None, transaction_type=None, old_balance=None, new_balance=None, fraud_probability=None):
    """Generate human-readable risk factors."""
    factors = []
    if amount and amount > 50000:
        factors.append("Very high transaction amount")
    elif amount and amount > 10000:
        factors.append("High transaction amount")
    if transaction_type and transaction_type.upper() in ["TRANSFER", "CASH_OUT"]:
        factors.append("High-risk transaction type")
    if old_balance is not None and new_balance is not None:
        change = abs(new_balance - old_balance)
        if old_balance > 0 and change / old_balance > 0.8:
            factors.append("Large balance change")
    if fraud_probability and fraud_probability > 0.7:
        factors.append("High ML fraud probability")
    elif fraud_probability and fraud_probability > 0.4:
        factors.append("Elevated ML fraud probability")
    return factors
