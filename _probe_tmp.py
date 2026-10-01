"""Throwaway: find a pg8000 connection recipe that works against Neon."""
import pathlib
import ssl
import sys

sys.path.insert(0, "sus-kigali-haircut")

import sqlalchemy as sa  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

env = {}
for line in pathlib.Path("sus-kigali-haircut/.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip()

pooled = make_url(env["DATABASE_URL"])
direct = make_url(env["DATABASE_URL_DIRECT"])
print("pooled host :", pooled.host)
print("direct host :", direct.host)
print("database    :", pooled.database, "| user:", pooled.username)
print()

cases = {
    "pooled  ssl_context": pooled,
    "direct  ssl_context": direct,
}

for label, base in cases.items():
    # Drop the libpq-only query string; pg8000 wants a real TLS context.
    url = base.set(drivername="postgresql+pg8000").set(query={})
    engine = None
    try:
        engine = sa.create_engine(
            url,
            connect_args={
                "ssl_context": ssl.create_default_context(),
                "timeout": 20,
            },
        )
        with engine.connect() as conn:
            row = conn.execute(
                sa.text("select current_database(), current_user")
            ).one()
            print(f"{label}  OK   -> {row[0]} / {row[1]}")
            tables = conn.execute(
                sa.text(
                    "select tablename from pg_tables "
                    "where schemaname='public' order by tablename"
                )
            ).scalars().all()
            print(f"{label}  tables -> {tables if tables else '(none yet)'}")
    except Exception as exc:  # noqa: BLE001
        print(f"{label}  FAIL -> {type(exc).__name__}: {str(exc)[:200]}")
    finally:
        if engine is not None:
            engine.dispose()

