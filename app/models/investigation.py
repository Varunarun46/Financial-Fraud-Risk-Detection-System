from datetime import datetime
from ..extensions import db


class Investigation(db.Model):
    __tablename__ = "investigations"

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("fraud_alerts.id"), nullable=True)
    transaction_id = db.Column(db.String(100), db.ForeignKey("transactions.transaction_id"), nullable=True)
    status = db.Column(db.String(30), default="OPEN", nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "alert_id": self.alert_id,
            "transaction_id": self.transaction_id,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
