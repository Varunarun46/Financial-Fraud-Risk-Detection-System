from flask import Blueprint, render_template
from ..auth import login_required, get_current_user

explainability_bp = Blueprint("explainability", __name__)


@explainability_bp.route("/explainability")
@login_required
def explain_page():
    user = get_current_user()
    return render_template("explainability/explain.html", user=user)
