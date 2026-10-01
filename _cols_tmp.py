"""Throwaway: confirm the commission columns exist in Postgres."""
import sys

sys.path.insert(0, "sus-kigali-haircut")

from sqlalchemy import inspect, text  # noqa: E402

from run import app  # noqa: E402
from sus import db  # noqa: E402

WANTED = {
    "services": ["commission_rate"],
    "transaction_items": ["commission_rate", "commission_amount"],
    "users": ["commission_rate"],
    "workers": ["commission_rate"],
}

with app.app_context():
    insp = inspect(db.engine)
    ok = True
    for table, cols in WANTED.items():
        have = {c["name"] for c in insp.get_columns(table)}
        for col in cols:
            mark = "OK  " if col in have else "MISS"
            if col not in have:
                ok = False
            print(f"  {mark} {table}.{col}")
    print()
    with db.engine.connect() as conn:
        ver = conn.execute(text("show server_version")).scalar()
        print("postgres server :", ver)
    print("all expected columns present:", ok)
