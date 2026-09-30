"""SUS Kigali Haircut — Website & Business Management System.

Usage:
    python run.py            start the server on http://127.0.0.1:5000
    python run.py init       create the database + owner login, then exit
    python run.py clean      drop every table and re-bootstrap an empty shop, then exit
    python run.py reseed     rebuild the database with the demo dataset, then exit
"""
import sys

from sus import create_app

app = create_app()

# Make sure the database exists and is usable. This has to happen at import
# time because serverless hosts (Vercel) import this module instead of running
# it as a script; locally `python run.py` benefits from it too.
with app.app_context():
    from sus import db, seed_data, ensure_schema
    db.create_all()
    ensure_schema()  # add columns added since the database was first created
    seed_data()      # bootstrap only: settings + owner login


def run_command(arg):
    """Handle the one-shot CLI commands. Returns True if the server must not start."""
    with app.app_context():
        from sus import db, seed_data, seed_demo, wipe_data, ensure_schema

        if arg == "init":
            db.create_all()
            ensure_schema()
            seed_data()
            print("Database ready. Owner login: owner@suskigali.rw / admin123")
            return True

        if arg == "clean":
            wipe_data()
            print("All data wiped. Clean shop ready — sign in and add your services.")
            return True

        if arg == "reseed":
            db.drop_all()
            db.create_all()
            seed_demo()
            print("Database reseeded with demo data.")
            return True

    return False


if __name__ == "__main__":
    command = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    # `python run.py reseed` used to reseed *and then* start a server, which
    # looked like a hang. Commands now finish and exit.
    if command and run_command(command):
        sys.exit(0)
    app.run(debug=True, host="127.0.0.1", port=5000)
