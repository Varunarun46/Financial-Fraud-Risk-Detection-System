from flask import Blueprint, request, jsonify, render_template
from ..auth import login_required, get_current_user
from ..extensions import db
from ..models import Transaction, FraudPrediction

transaction_bp = Blueprint("transactions", __name__)


@transaction_bp.route("/transactions")
@login_required
def transactions_page():
    user = get_current_user()
    return render_template("transactions/transactions.html", user=user)


@transaction_bp.route("/api/transactions", methods=["GET"])
@login_required
def get_transactions():
    """Get transactions with filtering, sorting, and pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    risk_level = request.args.get("risk_level", "")
    fraud_status = request.args.get("fraud_status", "")
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")

    query = Transaction.query

    if search:
        query = query.filter(
            (Transaction.transaction_id.ilike(f"%{search}%")) |
            (Transaction.source_account.ilike(f"%{search}%")) |
            (Transaction.destination_account.ilike(f"%{search}%"))
        )

    if fraud_status:
        if fraud_status == "fraud":
            query = query.filter(Transaction.is_fraud == True)
        elif fraud_status == "legitimate":
            query = query.filter(Transaction.is_fraud == False)

    if risk_level:
        query = query.join(
            FraudPrediction,
            Transaction.transaction_id == FraudPrediction.transaction_id
        ).filter(FraudPrediction.risk_level == risk_level.upper())

    # Sorting
    sort_column = getattr(Transaction, sort_by, Transaction.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Attach predictions
    transactions = []
    for tx in pagination.items:
        tx_dict = tx.to_dict()
        pred = FraudPrediction.query.filter_by(transaction_id=tx.transaction_id).first()
        if pred:
            tx_dict["prediction"] = pred.to_dict()
        transactions.append(tx_dict)

    return jsonify({
        "transactions": transactions,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    }), 200


@transaction_bp.route("/api/transactions/<tx_id>", methods=["GET"])
@login_required
def get_transaction(tx_id):
    """Get single transaction with prediction."""
    tx = Transaction.query.filter_by(transaction_id=tx_id).first()
    if not tx:
        return jsonify({"error": "Transaction not found"}), 404

    result = tx.to_dict()
    pred = FraudPrediction.query.filter_by(transaction_id=tx_id).first()
    if pred:
        result["prediction"] = pred.to_dict()

    return jsonify(result), 200
