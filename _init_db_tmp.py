"""Throwaway: provision the Neon database and report what landed in it."""
import sys

sys.path.insert(0, "sus-kigali-haircut")

from sqlalchemy import inspect  # noqa: E402

from run import app  # noqa: E402  (importing run.py creates schema + bootstraps)
from sus import db  # noqa: E402
from sus.models import (  # noqa: E402
    Appointment,
    Client,
    Service,
    Setting,
    Transaction,
    User,
    Worker,
)

with app.app_context():
    print("engine :", db.engine.url.render_as_string(hide_password=True))
    print("driver :", db.engine.dialect.name, "/", db.engine.dialect.driver)
    print()
    tables = inspect(db.engine).get_table_names()
    print(f"tables ({len(tables)}):")
    for name in tables:
        print("   -", name)
    print()
    for model, label in (
        (Setting, "settings"),
        (User, "users"),
        (Service, "services"),
        (Worker, "workers"),
        (Client, "clients"),
        (Appointment, "appointments"),
        (Transaction, "transactions"),
    ):
        print(f"   {label:<14} {model.query.count()}")
    print()
    for key in ("shop_name", "phone", "whatsapp"):
        row = Setting.query.filter_by(key=key).first()
        print(f"   setting {key:<10} {row.value if row else '(missing)'}")
