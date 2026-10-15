from datetime import datetime
from ..extensions import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    dataset_name = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(50))
    amount = db.Column(db.Numeric(18, 2))
    source_account = db.Column(db.String(150))
    destination_account = db.Column(db.String(150))
    old_balance_source = db.Column(db.Numeric(18, 2))
    new_balance_source = db.Column(db.Numeric(18, 2))
    old_balance_destination = db.Column(db.Numeric(18, 2))
    new_balance_destination = db.Column(db.Numeric(18, 2))
    transaction_timestamp = db.Column(db.DateTime)
    is_fraud = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    predictions = db.relationship("FraudPrediction", backref="transaction", lazy=True)
    alerts = db.relationship("FraudAlert", backref="transaction", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "dataset_name": self.dataset_name,
            "transaction_type": self.transaction_type,
            "amount": float(self.amount) if self.amount else None,
            "source_account": self.source_account,
            "destination_account": self.destination_account,
            "old_balance_source": float(self.old_balance_source) if self.old_balance_source else None,
            "new_balance_source": float(self.new_balance_source) if self.new_balance_source else None,
            "old_balance_destination": float(self.old_balance_destination) if self.old_balance_destination else None,
            "new_balance_destination": float(self.new_balance_destination) if self.new_balance_destination else None,
            "transaction_timestamp": self.transaction_timestamp.isoformat() if self.transaction_timestamp else None,
            "is_fraud": self.is_fraud,
        }
