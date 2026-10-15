from flask import Flask, session, request
from flask_cors import CORS

from .config import Config
from .extensions import db
from .models import (
    User, Transaction, FraudPrediction, FraudAlert,
    AuditLog, ModelResult, SystemSetting, Investigation,
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    db.init_app(app)

    # Register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    from .routes.health_routes import health_bp
    from .routes.dashboard_routes import dashboard_bp
    from .routes.prediction_routes import prediction_bp
    from .routes.transaction_routes import transaction_bp
    from .routes.alert_routes import alert_bp
    from .routes.admin_routes import admin_bp
    from .routes.report_routes import report_bp
    from .routes.anomaly_routes import anomaly_bp
    from .routes.model_routes import models_bp
    from .routes.explainability_routes import explainability_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(anomaly_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(explainability_bp)

    @app.before_request
    def sync_session_role():
        if "user_id" in session:
            user = User.query.get(session["user_id"])
            if user:
                session["role"] = user.role
                session["full_name"] = user.full_name

    with app.app_context():
        db.create_all()
        # Create default admin if no users exist
        if not User.query.first():
            admin = User(
                full_name="System Administrator",
                username="admin",
                email="admin@fraudsystem.local",
                role="ADMIN",
            )
            admin.set_password("Admin@123")
            db.session.add(admin)
            db.session.commit()
        # Seed sample data if database is empty
        from .services.seed_service import seed_if_empty
        seed_if_empty()

    return app
