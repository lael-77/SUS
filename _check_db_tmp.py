"""Throwaway: verify the app can reach the Neon Postgres database."""
import re
import sys

sys.path.insert(0, "sus-kigali-haircut")

import config  # noqa: E402

uri = config.Config.SQLALCHEMY_DATABASE_URI
print("resolved URI :", re.sub(r"://[^:]+:[^@]+@", "://USER:PW@", uri))
print("dialect      :", uri.split("://", 1)[0])
print()

import sqlalchemy as sa  # noqa: E402

engine = sa.create_engine(
    uri,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 20},
)

try:
    with engine.connect() as conn:
        print("CONNECTED OK")
        print("  server :", conn.execute(sa.text("select version()")).scalar()[:60])
        print("  db     :", conn.execute(sa.text("select current_database()")).scalar())
        print("  user   :", conn.execute(sa.text("select current_user")).scalar())
        names = conn.execute(
            sa.text(
                "select tablename from pg_tables "
                "where schemaname = 'public' order by tablename"
            )
        ).scalars().all()
        print("  tables :", names if names else "(none yet)")
except Exception as exc:  # noqa: BLE001
    print("CONNECT FAILED")
    print(" ", type(exc).__name__, str(exc)[:400])
    sys.exit(1)
finally:
    engine.dispose()
