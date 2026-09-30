import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Shop contact details — the ONE source of truth for the whole application.
#
# These values are written into the `settings` table the first time the
# database is created, and they are the fallback for every page: the top bar,
# the footer, the sticky mobile bar, "Call" buttons and every WhatsApp link.
# The owner can still change them live under Admin > Settings — once a row
# exists in the database that value wins.
# ---------------------------------------------------------------------------
SHOP_NAME = "SUS Kigali Haircut"
SHOP_PHONE = "+250 785 998 860"       # how the number is shown to people
SHOP_PHONE_TEL = "+250785998860"      # what href="tel:..." uses (no spaces)
SHOP_WHATSAPP = "250795410781"        # digits only, for https://wa.me/<n>


def database_uri():
    """Work out which database to talk to.

    1. ``DATABASE_URL`` / ``POSTGRES_URL`` — a managed Postgres such as
       Vercel Postgres, Neon, Supabase or Railway. Set it in the host's
       environment variables; see "Database" in README.md.
    2. ``VERCEL`` with no database URL — serverless filesystems are read-only
       apart from ``/tmp``, so SQLite has to live there.
    3. Anything else — a SQLite file next to this config file (local dev).
    """
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if url:
        # Hosts hand out "postgres://" (Heroku-style) or "postgresql://"
        # (Vercel Postgres). SQLAlchemy 2.x wants an explicit driver name.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                url = "postgresql+psycopg://" + url[len(prefix):]
                break
        return url
    if os.environ.get("VERCEL"):
        return "sqlite:///" + os.path.join("/tmp", "sus_kigali.db")
    return "sqlite:///" + os.path.join(BASE_DIR, "sus_kigali.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sus-kigali-haircut-dev-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Managed Postgres drops idle connections; pre-ping plus a short recycle
    # keeps the pooled connection healthy. Harmless for SQLite.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
