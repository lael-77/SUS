"""SUS KIGALI HAIRCUT — Website & Business Management System.

Usage:
    python run.py          -> start the server (http://127.0.0.1:5000)
    python run.py reseed   -> wipe database and recreate demo data
"""
from sus import create_app

app = create_app()

# Ensure the database exists and is seeded. This must run at import time
# because serverless hosts (Vercel) import this module instead of running
# it as a script; locally `python run.py` benefits from it too.
with app.app_context():
    from sus import db, seed_data
    db.create_all()
    seed_data()  # only seeds if database is empty

if __name__ == "__main__":
    import sys
    with app.app_context():
        from sus import db, seed_data
        if "reseed" in sys.argv:
            db.drop_all()
            db.create_all()
            seed_data()
            print("Database reseeded with demo data.")
    app.run(debug=True, host="127.0.0.1", port=5000)
