from datetime import datetime
from ..extensions import db


class ModelResult(db.Model):
    __tablename__ = "model_results"

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    dataset_name = db.Column(db.String(100), nullable=False)
    accuracy = db.Column(db.Numeric(8, 6))
    precision_score = db.Column(db.Numeric(8, 6))
    recall_score = db.Column(db.Numeric(8, 6))
    f1_score = db.Column(db.Numeric(8, 6))
    roc_auc = db.Column(db.Numeric(8, 6))
    pr_auc = db.Column(db.Numeric(8, 6))
    training_seconds = db.Column(db.Numeric(12, 4))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "model_name": self.model_name,
            "dataset_name": self.dataset_name,
            "accuracy": float(self.accuracy) if self.accuracy else None,
            "precision": float(self.precision_score) if self.precision_score else None,
            "recall": float(self.recall_score) if self.recall_score else None,
            "f1_score": float(self.f1_score) if self.f1_score else None,
            "roc_auc": float(self.roc_auc) if self.roc_auc else None,
            "pr_auc": float(self.pr_auc) if self.pr_auc else None,
            "training_seconds": float(self.training_seconds) if self.training_seconds else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
