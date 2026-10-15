"""Seed the database with realistic sample data (idempotent)."""
import random
from datetime import datetime, timedelta
from pathlib import Path
from ..extensions import db
from ..models import Transaction, FraudPrediction, FraudAlert, ModelResult

BASE_DIR = Path(__file__).resolve().parents[2]


def seed_if_empty():
    """Seed the database only if it's empty."""
    if Transaction.query.count() > 0:
        return False  # Already seeded

    random.seed(42)
    TX_TYPES = ["TRANSFER", "CASH_OUT", "CASH_IN", "PAYMENT", "DEBIT"]
    MODELS = ["XGBoost", "LightGBM", "RandomForest", "LogisticRegression", "NeuralNetwork"]
    DATASETS = ["credit_card", "paysim"]

    # Transactions
    tx_ids = []
    for i in range(500):
        is_fraud = 1 if random.random() < 0.05 else 0
        amount = round(random.uniform(10, 50000) * (3 if is_fraud else 1), 2)
        tx_id = f"TXN{datetime.now().strftime('%Y%m%d')}{i:06d}"
        tx_ids.append((tx_id, is_fraud))
        ts = datetime.now() - timedelta(hours=random.uniform(0, 720))
        db.session.add(Transaction(
            transaction_id=tx_id,
            dataset_name=random.choice(DATASETS),
            transaction_type=random.choice(TX_TYPES),
            amount=amount,
            source_account=f"ACC{random.randint(10000, 99999)}",
            destination_account=f"ACC{random.randint(10000, 99999)}",
            old_balance_source=round(random.uniform(1000, 100000), 2),
            new_balance_source=round(random.uniform(0, 100000), 2),
            old_balance_destination=round(random.uniform(0, 50000), 2),
            new_balance_destination=round(random.uniform(0, 50000), 2),
            transaction_timestamp=ts,
            is_fraud=bool(is_fraud),
        ))

    # Predictions
    for tx_id, is_fraud in tx_ids:
        fraud_prob = round(random.uniform(0.6, 0.99) if is_fraud else round(random.uniform(0.01, 0.4), 4), 4)
        risk_score = round(fraud_prob * 100, 2)
        risk_level = "HIGH" if risk_score >= 70 else ("MEDIUM" if risk_score >= 40 else "LOW")
        prediction = "FRAUD" if fraud_prob >= 0.5 else "LEGITIMATE"
        db.session.add(FraudPrediction(
            transaction_id=tx_id,
            model_name=random.choice(MODELS),
            fraud_probability=fraud_prob,
            risk_score=risk_score,
            risk_level=risk_level,
            prediction=prediction,
            anomaly_score=round(random.uniform(0, 1), 4),
        ))

    # Model results
    for model in MODELS:
        for dataset in DATASETS:
            acc = round(random.uniform(0.85, 0.99), 4)
            prec = round(random.uniform(0.75, 0.95), 4)
            rec = round(random.uniform(0.70, 0.92), 4)
            f1 = round(2 * prec * rec / (prec + rec), 4) if (prec + rec) > 0 else 0
            db.session.add(ModelResult(
                model_name=model,
                dataset_name=dataset,
                accuracy=acc,
                precision_score=prec,
                recall_score=rec,
                f1_score=f1,
                roc_auc=round(random.uniform(0.88, 0.99), 4),
                pr_auc=round(random.uniform(0.80, 0.96), 4),
                training_seconds=round(random.uniform(5, 120), 2),
            ))

    # Alerts
    ALERT_TITLES = [
        "Unusual transfer amount detected", "High-risk transaction pattern",
        "Velocity check failed", "Account takeover suspected",
        "Anomalous cash-out behavior", "Cross-border fraud indicator",
        "Multiple failed attempts", "Device fingerprint mismatch",
    ]
    for i in range(25):
        tx_id, _ = random.choice(tx_ids)
        severity = random.choice(["HIGH", "MEDIUM", "LOW"])
        status = random.choice(["OPEN", "OPEN", "OPEN", "RESOLVED", "INVESTIGATING"])
        ts = datetime.now() - timedelta(hours=random.uniform(0, 168))
        db.session.add(FraudAlert(
            alert_id=f"ALT-{random.randint(100000, 999999)}",
            transaction_id=tx_id,
            severity=severity,
            title=random.choice(ALERT_TITLES),
            message="Automated fraud detection alert triggered.",
            status=status,
            created_at=ts,
        ))

    db.session.commit()
    return True
