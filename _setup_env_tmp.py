"""Throwaway: build sus-kigali-haircut/.env from the pulled Vercel env."""
import pathlib
import re
import secrets

here = pathlib.Path(__file__).parent
pulled = here / ".env.pulled"

values = {}
for line in pulled.read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, _, val = line.partition("=")
    values[key.strip()] = val.strip().strip('"').strip("'")

pooled = values["POSTGRES_URL"]
direct = values["POSTGRES_URL_NON_POOLING"]


def mask(url: str) -> str:
    return re.sub(r"://[^:]+:[^@]+@", "://USER:PW@", url)


body = f"""# Local environment for SUS Kigali Haircut.
#
# Points at the Neon Postgres database attached to the Vercel project
# `sus-m1mn` (scope laels-projects-689d0398). Gitignored - never commit it,
# and never paste this URL into a template or any other public file.
#
# Regenerate after a `vercel env pull`:
#     vercel env pull .env.pulled --environment=production
#
# Leave DATABASE_URL unset (or delete this file) to fall back to the local
# SQLite file `sus_kigali.db`.

# The pooled Neon endpoint. SQLAlchemy keeps its own connection pool and
# config.py pre-pings + recycles connections, so the pooler is safe here.
DATABASE_URL={pooled}

# The same database, direct (no PgBouncer). Handy for one-off scripts and
# for `psql`; swap it into DATABASE_URL if the pooler ever misbehaves.
DATABASE_URL_DIRECT={direct}

# Signs session cookies. Rotate before going live.
SECRET_KEY={secrets.token_hex(32)}
"""

out = here / "sus-kigali-haircut" / ".env"
out.write_text(body, encoding="utf-8", newline="\n")

print(f"wrote {out}  ({out.stat().st_size} bytes)")
print()
print("DATABASE_URL        =", mask(pooled))
print("DATABASE_URL_DIRECT =", mask(direct))
print("SECRET_KEY          = <64 hex chars>")
