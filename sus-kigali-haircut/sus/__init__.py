"""SUS KIGALI HAIRCUT — Flask application factory."""
import os

from flask import Flask

from config import Config
from .models import db

# expose for run.py: `from sus import db, seed_data`
from .seed import seed_data  # noqa: E402,F401 (after models to avoid circular import)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from .public import public_bp
    from .admin import admin_bp
    from .api import api_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # template filter for RWF money formatting: {{ 10000|rwf }} -> "10,000 RWF"
    @app.template_filter("rwf")
    def rwf(value):
        try:
            return f"{int(value):,} RWF"
        except (TypeError, ValueError):
            return value

    # make current user name available to admin templates
    @app.context_processor
    def inject_user():
        from .auth import current_user
        u = current_user()
        return {"current_user_name": u.name if u else ""}

    return app
