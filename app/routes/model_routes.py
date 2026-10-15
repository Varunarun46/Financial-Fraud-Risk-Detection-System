from flask import Blueprint, render_template
from ..auth import login_required, get_current_user

models_bp = Blueprint("models", __name__)


@models_bp.route("/models")
@login_required
def models_page():
    user = get_current_user()
    return render_template("models/models.html", user=user)
