"""Seed the database with realistic sample data for dashboard demonstration."""
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "instance" / "financial_fraud.db"

random.seed(42)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
cursor.executescript("""
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    transaction_type TEXT,
    amount REAL,
    source_account TEXT,
    destination_account TEXT,
    old_balance_source REAL,
    new_balance_source REAL,
    old_balance_destination REAL,
    new_balance_destination REAL,
    transaction_timestamp TEXT,
    is_fraud INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fraud_predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    model_name TEXT NOT NULL,
    fraud_probability REAL,
    risk_score REAL,
    risk_level TEXT,
    prediction TEXT,
    explanation TEXT,
    predicted_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_results (
    model_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    accuracy REAL,
    precision_score REAL,
    recall_score REAL,
    f1_score REAL,
    roc_auc REAL,
    pr_auc REAL,
    training_seconds REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

# Generate transactions
TX_TYPES = ["TRANSFER", "CASH_OUT", "CASH_IN", "PAYMENT", "DEBIT"]
MODELS = ["XGBoost", "LightGBM", "RandomForest", "LogisticRegression", "NeuralNetwork"]
DATASETS = ["credit_card", "paysim"]

tx_ids = []
for i in range(500):
    is_fraud = 1 if random.random() < 0.05 else 0
    amount = round(random.uniform(10, 50000) * (3 if is_fraud else 1), 2)
    tx_id = f"TXN{datetime.now().strftime('%Y%m%d')}{i:06d}"
    tx_ids.append((tx_id, is_fraud))
    ts = (datetime.now() - timedelta(hours=random.uniform(0, 720))).isoformat()
    cursor.execute(
        "INSERT INTO transactions (transaction_id, dataset_name, transaction_type, amount, source_account, destination_account, old_balance_source, new_balance_source, old_balance_destination, new_balance_destination, transaction_timestamp, is_fraud) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            tx_id,
            random.choice(DATASETS),
            random.choice(TX_TYPES),
            amount,
            f"ACC{random.randint(10000, 99999)}",
            f"ACC{random.randint(10000, 99999)}",
            round(random.uniform(1000, 100000), 2),
            round(random.uniform(0, 100000), 2),
            round(random.uniform(0, 50000), 2),
            round(random.uniform(0, 50000), 2),
            ts,
            is_fraud,
        ),
    )

# Generate predictions
for tx_id, is_fraud in tx_ids:
    fraud_prob = round(random.uniform(0.6, 0.99) if is_fraud else round(random.uniform(0.01, 0.4), 4), 4)
    risk_score = round(fraud_prob * 100, 2)
    risk_level = "HIGH" if risk_score >= 70 else ("MEDIUM" if risk_score >= 40 else "LOW")
    prediction = "FRAUD" if fraud_prob >= 0.5 else "LEGITIMATE"
    model = random.choice(MODELS)
    cursor.execute(
        "INSERT INTO fraud_predictions (transaction_id, model_name, fraud_probability, risk_score, risk_level, prediction, explanation) VALUES (?,?,?,?,?,?,?)",
        (tx_id, model, fraud_prob, risk_score, risk_level, prediction, "{}"),
    )

# Generate model results
for model in MODELS:
    for dataset in DATASETS:
        acc = round(random.uniform(0.85, 0.99), 4)
        prec = round(random.uniform(0.75, 0.95), 4)
        rec = round(random.uniform(0.70, 0.92), 4)
        f1 = round(2 * prec * rec / (prec + rec), 4) if (prec + rec) > 0 else 0
        roc = round(random.uniform(0.88, 0.99), 4)
        pr = round(random.uniform(0.80, 0.96), 4)
        cursor.execute(
            "INSERT INTO model_results (model_name, dataset_name, accuracy, precision_score, recall_score, f1_score, roc_auc, pr_auc, training_seconds) VALUES (?,?,?,?,?,?,?,?,?)",
            (model, dataset, acc, prec, rec, f1, roc, pr, round(random.uniform(5, 120), 2)),
        )

# Generate alerts
ALERT_TITLES = [
    "Unusual transfer amount detected",
    "High-risk transaction pattern",
    "Velocity check failed",
    "Account takeover suspected",
    "Anomalous cash-out behavior",
    "Cross-border fraud indicator",
    "Multiple failed attempts",
    "Device fingerprint mismatch",
]
for i in range(25):
    tx_id, _ = random.choice(tx_ids)
    severity = random.choice(["HIGH", "MEDIUM", "LOW"])
    status = random.choice(["OPEN", "OPEN", "OPEN", "RESOLVED", "INVESTIGATING"])
    ts = (datetime.now() - timedelta(hours=random.uniform(0, 168))).isoformat()
    cursor.execute(
        "INSERT INTO alerts (transaction_id, severity, title, message, status, created_at) VALUES (?,?,?,?,?,?)",
        (tx_id, severity, random.choice(ALERT_TITLES), "Automated fraud detection alert triggered.", status, ts),
    )

conn.commit()
conn.close()
print(f"Seeded {len(tx_ids)} transactions, predictions, model results, and alerts.")
