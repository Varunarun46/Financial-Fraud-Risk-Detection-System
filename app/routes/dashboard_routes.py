from flask import Blueprint, jsonify, render_template, current_app
from sqlalchemy import text
from pathlib import Path
import json

from ..extensions import db

dashboard_bp = Blueprint("dashboard_bp", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@dashboard_bp.route("/api/dashboard/stats")
def dashboard_stats():
    """Aggregate stats for the dashboard."""

    # --- Database table counts ---
    table_counts = {}
    try:
        tables = db.session.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        ).fetchall()
        for (table_name,) in tables:
            if table_name.startswith("sqlite_"):
                continue
            count = db.session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            ).scalar()
            table_counts[table_name] = count
    except Exception:
        pass

    # --- Dataset file info ---
    base_dir = Path(current_app.config.get("BASE_DIR", Path(__file__).resolve().parents[2]))
    raw_dir = base_dir / "data" / "raw"
    dataset_info = []
    for folder_name, display_name in [
        ("credit_card", "Credit Card Fraud (ULB)"),
        ("paysim", "PaySim"),
    ]:
        folder = raw_dir / folder_name
        csv_files = list(folder.rglob("*.csv")) if folder.exists() else []
        total_size = sum(f.stat().st_size for f in csv_files)
        dataset_info.append({
            "name": display_name,
            "folder": folder_name,
            "file_count": len(csv_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": [f.name for f in csv_files],
        })

    # --- Fraud stats from transactions table ---
    fraud_stats = {
        "total_transactions": 0,
        "fraud_count": 0,
        "legitimate_count": 0,
        "fraud_rate": 0,
        "total_value": 0,
        "fraud_value": 0,
    }
    try:
        row = db.session.execute(
            text(
                "SELECT COUNT(*), "
                "SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END), "
                "SUM(amount), "
                "SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END) "
                "FROM transactions"
            )
        ).fetchone()
        if row:
            total, fraud = row[0] or 0, row[1] or 0
            fraud_stats["total_transactions"] = total
            fraud_stats["fraud_count"] = fraud
            fraud_stats["legitimate_count"] = total - fraud
            fraud_stats["fraud_rate"] = round(fraud / total * 100, 4) if total else 0
            fraud_stats["total_value"] = float(row[2]) if row[2] else 0
            fraud_stats["fraud_value"] = float(row[3]) if row[3] else 0
    except Exception:
        pass

    # --- Model results ---
    model_results = []
    try:
        rows = db.session.execute(
            text(
                "SELECT model_name, dataset_name, accuracy, precision_score, "
                "recall_score, f1_score, roc_auc, pr_auc "
                "FROM model_results ORDER BY created_at DESC"
            )
        ).fetchall()
        for r in rows:
            model_results.append({
                "model_name": r[0],
                "dataset_name": r[1],
                "accuracy": float(r[2]) if r[2] else None,
                "precision": float(r[3]) if r[3] else None,
                "recall": float(r[4]) if r[4] else None,
                "f1_score": float(r[5]) if r[5] else None,
                "roc_auc": float(r[6]) if r[6] else None,
                "pr_auc": float(r[7]) if r[7] else None,
            })
    except Exception:
        pass

    # --- Risk level distribution ---
    risk_distribution = []
    try:
        rows = db.session.execute(
            text(
                "SELECT risk_level, COUNT(*) as cnt "
                "FROM fraud_predictions GROUP BY risk_level"
            )
        ).fetchall()
        for r in rows:
            risk_distribution.append({"level": r[0], "count": r[1]})
    except Exception:
        pass

    # --- Recent alerts ---
    recent_alerts = []
    try:
        rows = db.session.execute(
            text(
                "SELECT alert_id, severity, title, status, created_at "
                "FROM fraud_alerts ORDER BY created_at DESC LIMIT 10"
            )
        ).fetchall()
        for r in rows:
            recent_alerts.append({
                "id": r[0],
                "severity": r[1],
                "title": r[2],
                "status": r[3],
                "created_at": str(r[4]),
            })
    except Exception:
        pass

    # --- Recent predictions ---
    recent_predictions = []
    try:
        rows = db.session.execute(
            text(
                "SELECT fp.id, fp.transaction_id, fp.model_name, "
                "fp.fraud_probability, fp.risk_score, fp.risk_level, fp.prediction, "
                "fp.predicted_at "
                "FROM fraud_predictions fp "
                "ORDER BY fp.predicted_at DESC LIMIT 20"
            )
        ).fetchall()
        for r in rows:
            recent_predictions.append({
                "id": r[0],
                "transaction_id": r[1],
                "model_name": r[2],
                "fraud_probability": float(r[3]) if r[3] else None,
                "risk_score": float(r[4]) if r[4] else None,
                "risk_level": r[5],
                "prediction": r[6],
                "predicted_at": str(r[7]),
            })
    except Exception:
        pass

    # --- Risk distribution ---
    risk_distribution = []
    try:
        rows = db.session.execute(
            text(
                "SELECT risk_level, COUNT(*) as cnt "
                "FROM fraud_predictions GROUP BY risk_level"
            )
        ).fetchall()
        for r in rows:
            risk_distribution.append({"level": r[0], "count": r[1]})
    except Exception:
        pass

    # --- Hourly transaction volume (last 24h) ---
    hourly_volume = []
    try:
        rows = db.session.execute(
            text(
                "SELECT strftime('%H', transaction_timestamp) as hour, "
                "COUNT(*) as cnt, "
                "SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_cnt "
                "FROM transactions "
                "WHERE transaction_timestamp >= datetime('now', '-24 hours') "
                "GROUP BY hour ORDER BY hour"
            )
        ).fetchall()
        for r in rows:
            hourly_volume.append({
                "hour": r[0],
                "count": r[1],
                "fraud_count": r[2] or 0,
            })
    except Exception:
        pass

    # --- Alert severity distribution ---
    alert_severity = []
    try:
        rows = db.session.execute(
            text(
                "SELECT severity, COUNT(*) as cnt "
                "FROM alerts GROUP BY severity"
            )
        ).fetchall()
        for r in rows:
            alert_severity.append({"severity": r[0], "count": r[1]})
    except Exception:
        pass

    return jsonify({
        "table_counts": table_counts,
        "datasets": dataset_info,
        "fraud_stats": fraud_stats,
        "model_results": model_results,
        "risk_distribution": risk_distribution,
        "recent_alerts": recent_alerts,
        "recent_predictions": recent_predictions,
        "hourly_volume": hourly_volume,
        "alert_severity": alert_severity,
    })


@dashboard_bp.route("/api/dashboard/health")
def dashboard_health():
    """Extended health info for the dashboard."""
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    base_dir = Path(current_app.config.get("BASE_DIR", Path(__file__).resolve().parents[2]))
    raw_dir = base_dir / "data" / "raw"
    datasets_present = {
        "credit_card": (raw_dir / "credit_card").exists(),
        "paysim": (raw_dir / "paysim").exists(),
    }

    return jsonify({
        "status": "ok",
        "database": db_status,
        "datasets_present": datasets_present,
        "phase": 1,
    })
