"""ML model training and prediction service."""
import os
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
)
from ..extensions import db
from ..models import ModelResult, Transaction

BASE_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = BASE_DIR / "trained_models"
MODELS_DIR.mkdir(exist_ok=True)

MODEL_REGISTRY = {}


def load_datasets():
    """Load and return available datasets."""
    data_dir = BASE_DIR / "data" / "raw"
    datasets = {}

    # Credit Card dataset
    cc_path = data_dir / "credit_card" / "creditcard.csv"
    if cc_path.exists():
        df = pd.read_csv(cc_path)
        datasets["credit_card"] = df

    # PaySim dataset (read max 100k rows for memory)
    ps_path = data_dir / "paysim" / "PS_20174392719_1491204439457_log.csv"
    if ps_path.exists():
        df = pd.read_csv(ps_path, nrows=100000)
        datasets["paysim"] = df

    return datasets


def preprocess_credit_card(df):
    """Preprocess ULB Credit Card dataset."""
    features = df.drop(columns=["Class", "Time"], errors="ignore")
    target = df["Class"]
    return features, target


def preprocess_paysim(df):
    """Preprocess PaySim dataset."""
    df = df.copy()
    # Encode transaction type
    type_map = {"CASH_IN": 0, "CASH_OUT": 1, "DEBIT": 2, "PAYMENT": 3, "TRANSFER": 4}
    df["type_encoded"] = df["type"].map(type_map).fillna(0)

    # Feature engineering
    df["balance_diff_source"] = df["oldbalanceOrg"] - df["newbalanceOrig"]
    df["balance_diff_dest"] = df["newbalanceDest"] - df["oldbalanceDest"]
    df["amount_to_balance_ratio"] = df["amount"] / (df["oldbalanceOrg"] + 1)

    feature_cols = [
        "step", "type_encoded", "amount",
        "oldbalanceOrg", "newbalanceOrig",
        "oldbalanceDest", "newbalanceDest",
        "balance_diff_source", "balance_diff_dest",
        "amount_to_balance_ratio",
    ]
    features = df[feature_cols]
    target = df["isFraud"]
    return features, target


def train_models(dataset_name="credit_card"):
    """Train all ML models on the specified dataset."""
    datasets = load_datasets()
    if dataset_name not in datasets:
        return {"error": f"Dataset '{dataset_name}' not found"}

    df = datasets[dataset_name]

    if dataset_name == "credit_card":
        X, y = preprocess_credit_card(df)
    elif dataset_name == "paysim":
        X, y = preprocess_paysim(df)
    else:
        return {"error": "Unknown dataset"}

    # Downsample if too large (max 50k rows for memory)
    if len(X) > 50000:
        from sklearn.utils import resample
        # Keep all fraud samples + sample legitimate
        fraud_idx = y[y == 1].index
        legit_idx = y[y == 0].index
        n_legit = min(45000, len(legit_idx))
        n_fraud = min(5000, len(fraud_idx))
        sampled_idx = list(resample(legit_idx, n_samples=n_legit, random_state=42, replace=False)) + \
                      list(resample(fraud_idx, n_samples=n_fraud, random_state=42, replace=False))
        X = X.loc[sampled_idx]
        y = y.loc[sampled_idx]

    # Handle class imbalance with class weights
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save scaler
    with open(MODELS_DIR / f"{dataset_name}_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    results = []
    class_weight = "balanced"

    # 1. Logistic Regression
    lr = LogisticRegression(class_weight=class_weight, max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    y_pred = lr.predict(X_test_scaled)
    y_prob = lr.predict_proba(X_test_scaled)[:, 1]
    results.append(_evaluate("LogisticRegression", dataset_name, y_test, y_pred, y_prob, lr, X_train_scaled, y_train))
    _save_model(lr, dataset_name, "logistic_regression")

    # 2. Decision Tree
    dt = DecisionTreeClassifier(class_weight=class_weight, max_depth=10, random_state=42)
    dt.fit(X_train, y_train)
    y_pred = dt.predict(X_test)
    y_prob = dt.predict_proba(X_test)[:, 1]
    results.append(_evaluate("DecisionTree", dataset_name, y_test, y_pred, y_prob, dt, X_train, y_train))
    _save_model(dt, dataset_name, "decision_tree")

    # 3. Random Forest
    rf = RandomForestClassifier(
        n_estimators=100, class_weight=class_weight,
        max_depth=10, random_state=42, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)[:, 1]
    results.append(_evaluate("RandomForest", dataset_name, y_test, y_pred, y_prob, rf, X_train, y_train))
    _save_model(rf, dataset_name, "random_forest")

    # 4. Isolation Forest (anomaly detection)
    iso = IsolationForest(contamination=0.01, random_state=42, n_jobs=-1)
    iso.fit(X_train_scaled)
    y_pred_iso = iso.predict(X_test_scaled)
    y_pred_iso = (y_pred_iso == -1).astype(int)  # -1 = anomaly
    y_prob_iso = -iso.score_samples(X_test_scaled)  # Higher = more anomalous
    y_prob_iso = (y_prob_iso - y_prob_iso.min()) / (y_prob_iso.max() - y_prob_iso.min() + 1e-10)
    results.append(_evaluate("IsolationForest", dataset_name, y_test, y_pred_iso, y_prob_iso, iso, X_train_scaled, y_train))
    _save_model(iso, dataset_name, "isolation_forest")

    # Store results in database
    for r in results:
        mr = ModelResult(
            model_name=r["model_name"],
            dataset_name=dataset_name,
            accuracy=r["accuracy"],
            precision_score=r["precision"],
            recall_score=r["recall"],
            f1_score=r["f1"],
            roc_auc=r["roc_auc"],
            pr_auc=r["pr_auc"],
            training_seconds=r["training_seconds"],
        )
        db.session.add(mr)
    db.session.commit()

    return {"message": f"Trained {len(results)} models on {dataset_name}", "results": [r["model_name"] for r in results]}


def _evaluate(model_name, dataset_name, y_test, y_pred, y_prob, model, X_train, y_train):
    """Evaluate a trained model."""
    import time
    start = time.time()
    # Prediction time
    if hasattr(model, "predict_proba"):
        _ = model.predict_proba(X_train[:100])
    else:
        _ = model.predict(X_train[:100])
    pred_time = (time.time() - start) / 100

    cm = confusion_matrix(y_test, y_pred)
    return {
        "model_name": model_name,
        "dataset_name": dataset_name,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "pr_auc": float(average_precision_score(y_test, y_prob)),
        "training_seconds": 0,
        "prediction_time": pred_time,
        "confusion_matrix": cm.tolist(),
    }


def _save_model(model, dataset_name, model_key):
    """Save trained model to disk."""
    path = MODELS_DIR / f"{dataset_name}_{model_key}.pkl"
    with open(path, "wb") as f:
        pickle.dump(model, f)


def load_model(dataset_name, model_key):
    """Load a trained model from disk."""
    path = MODELS_DIR / f"{dataset_name}_{model_key}.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def predict_transaction(dataset_name, model_key, transaction_data):
    """Make a fraud prediction for a single transaction."""
    model = load_model(dataset_name, model_key)
    if not model:
        return {"error": "Model not found. Train models first."}

    scaler_path = MODELS_DIR / f"{dataset_name}_scaler.pkl"
    scaler = None
    if scaler_path.exists():
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)

    # Build feature vector
    if dataset_name == "credit_card":
        features = _build_cc_features(transaction_data)
    elif dataset_name == "paysim":
        features = _build_paysim_features(transaction_data)
    else:
        return {"error": "Unknown dataset"}

    X = np.array(features).reshape(1, -1)
    if scaler and model_key in ["logistic_regression", "isolation_forest"]:
        X = scaler.transform(X)

    if hasattr(model, "predict_proba"):
        prob = float(model.predict_proba(X)[0][1])
    else:
        prob = float(model.predict(X)[0])

    # Anomaly score from Isolation Forest
    iso = load_model(dataset_name, "isolation_forest")
    anomaly_score = 0
    if iso:
        if scaler:
            X_scaled = scaler.transform(X)
        else:
            X_scaled = X
        anomaly_score = float(-iso.score_samples(X_scaled)[0])
        anomaly_score = (anomaly_score - (-0.5)) / (0.5 - (-0.5))  # Normalize
        anomaly_score = max(0, min(1, anomaly_score))

    return {
        "fraud_probability": round(prob, 4),
        "anomaly_score": round(anomaly_score, 4),
        "model": model_key,
    }


def _build_cc_features(data):
    """Build feature vector for credit card transaction."""
    # V1-V28 + Amount
    features = []
    for i in range(1, 29):
        features.append(data.get(f"V{i}", 0))
    features.append(data.get("Amount", 0))
    return features


def _build_paysim_features(data):
    """Build feature vector for PaySim transaction."""
    type_map = {"CASH_IN": 0, "CASH_OUT": 1, "DEBIT": 2, "PAYMENT": 3, "TRANSFER": 4}
    tx_type = type_map.get(data.get("type", ""), 0)
    amount = data.get("amount", 0)
    old_bal = data.get("oldbalanceOrg", 0)
    new_bal = data.get("newbalanceOrig", 0)
    old_dest = data.get("oldbalanceDest", 0)
    new_dest = data.get("newbalanceDest", 0)
    step = data.get("step", 0)

    return [
        step, tx_type, amount,
        old_bal, new_bal, old_dest, new_dest,
        old_bal - new_bal, new_dest - old_dest,
        amount / (old_bal + 1),
    ]


def get_feature_importance(dataset_name, model_key="random_forest"):
    """Get feature importance from a trained model."""
    model = load_model(dataset_name, model_key)
    if not model or not hasattr(model, "feature_importances_"):
        return None

    if dataset_name == "credit_card":
        feature_names = [f"V{i}" for i in range(1, 29)] + ["Amount"]
    else:
        feature_names = [
            "step", "type_encoded", "amount",
            "oldbalanceOrg", "newbalanceOrig",
            "oldbalanceDest", "newbalanceDest",
            "balance_diff_source", "balance_diff_dest",
            "amount_to_balance_ratio",
        ]

    importances = model.feature_importances_
    return sorted(
        [{"feature": f, "importance": float(i)} for f, i in zip(feature_names, importances)],
        key=lambda x: x["importance"],
        reverse=True,
    )
