import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Vercel (serverless) has a read-only filesystem except /tmp,
# so the SQLite database must live there in production.
if os.environ.get("VERCEL"):
    DB_PATH = os.path.join("/tmp", "sus_kigali.db")
else:
    DB_PATH = os.path.join(BASE_DIR, "sus_kigali.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sus-kigali-haircut-dev-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
