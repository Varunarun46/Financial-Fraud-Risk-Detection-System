from datetime import datetime
from ..extensions import db


class FraudPrediction(db.Model):
    __tablename__ = "fraud_predictions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), db.ForeignKey("transactions.transaction_id"), nullable=True)
    model_name = db.Column(db.String(100), nullable=False)
    fraud_probability = db.Column(db.Numeric(8, 6))
    risk_score = db.Column(db.Numeric(6, 2))
    risk_level = db.Column(db.String(30))
    prediction = db.Column(db.String(30))
    anomaly_score = db.Column(db.Numeric(8, 6), default=0)
    explanation = db.Column(db.Text)
    predicted_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "model_name": self.model_name,
            "fraud_probability": float(self.fraud_probability) if self.fraud_probability else None,
            "risk_score": float(self.risk_score) if self.risk_score else None,
            "risk_level": self.risk_level,
            "prediction": self.prediction,
            "anomaly_score": float(self.anomaly_score) if self.anomaly_score else None,
            "explanation": self.explanation,
            "predicted_at": self.predicted_at.isoformat() if self.predicted_at else None,
        }
