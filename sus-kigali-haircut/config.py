import os
import ssl

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _load_env_file():
    """Pull ``KEY=value`` pairs out of a ``.env`` file next to this file.

    This is a local convenience only. Real environment variables always win
    (``setdefault``), so on Vercel — where the platform injects
    ``DATABASE_URL`` itself — this quietly does nothing. The file is
    gitignored; never commit real credentials.
    """
    path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


_load_env_file()

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


# Managed Postgres drops idle connections; pre-ping plus a short recycle keeps
# the pooled connection healthy. Harmless for SQLite.
BASE_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}


def _postgres_driver():
    """Return the SQLAlchemy dialect prefix for a driver this machine can run.

    ``psycopg`` is the fast one and the right choice on the Linux container
    Vercel builds, so it is always tried first. Windows machines with Smart
    App Control switched on sometimes refuse to load its compiled ``pq``
    extension; ``pg8000`` is pure Python and therefore cannot be blocked, so
    it is the fallback.
    """
    for module, dialect in (("psycopg", "postgresql+psycopg"),
                            ("pg8000", "postgresql+pg8000")):
        try:
            __import__(module)
        except ImportError:
            continue
        return dialect
    return "postgresql+psycopg"  # nothing loaded — let SQLAlchemy explain why


def _database_settings():
    """Return ``(uri, engine_options)`` for whichever database to talk to.

    1. ``DATABASE_URL`` / ``POSTGRES_URL`` — a managed Postgres such as
       Vercel Postgres, Neon, Supabase or Railway. Set it in the host's
       environment variables; see "Database" in README.md.
    2. ``VERCEL`` with no database URL — serverless filesystems are read-only
       apart from ``/tmp``, so SQLite has to live there.
    3. Anything else — a SQLite file next to this config file (local dev).
    """
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        if os.environ.get("VERCEL"):
            where = os.path.join("/tmp", "sus_kigali.db")
        else:
            where = os.path.join(BASE_DIR, "sus_kigali.db")
        return "sqlite:///" + where, dict(BASE_ENGINE_OPTIONS)

    # Hosts hand out "postgres://" (Heroku-style) or "postgresql://" (Vercel
    # Postgres). SQLAlchemy 2.x wants an explicit driver name. A URL that
    # already names one is left exactly as the operator wrote it.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = _postgres_driver() + "://" + url[len(prefix):]
            break

    options = dict(BASE_ENGINE_OPTIONS)
    if url.startswith("postgresql+pg8000://"):
        # pg8000 does not read libpq's `sslmode` / `channel_binding` query
        # parameters. Managed hosts always demand TLS, so honour that with a
        # real SSL context and drop the query string it cannot parse.
        needs_tls = "sslmode=require" in url or "sslmode=verify" in url
        url = url.split("?", 1)[0]
        if needs_tls:
            options["connect_args"] = {"ssl_context": ssl.create_default_context()}
    return url, options


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sus-kigali-haircut-dev-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS = _database_settings()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
