"""Smoke test: seed the DB and hit every route with Flask's test client.

Run it from the project root:  python smoke_test.py

It always runs against a throwaway SQLite file in the system temp directory,
never the configured database, so it is safe to run at any time — including
when ``.env`` points at a live Postgres instance.
"""
import os
import sys, io
import tempfile

# Force a disposable database *before* anything imports `config`, which reads
# DATABASE_URL once at import time. `_load_env_file()` uses setdefault(), so an
# explicit value here always wins over `.env`.
_SMOKE_DB = os.path.join(tempfile.gettempdir(), "sus_smoke_test.db")
if os.path.exists(_SMOKE_DB):
    os.remove(_SMOKE_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _SMOKE_DB

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sus import create_app, db, seed_data, seed_demo, ensure_schema

app = create_app()

# Belt and braces: refuse to continue if we somehow ended up on a real server.
with app.app_context():
    backend = db.engine.url.get_backend_name()
    if backend != "sqlite":
        raise SystemExit(
            f"Refusing to run: smoke_test needs a throwaway SQLite database, "
            f"but got {backend!r}. It would drop every table."
        )

with app.app_context():
    db.drop_all()
    db.create_all()
    ensure_schema()
    seed_data()          # bootstrap: settings + owner login
    seed_demo()          # illustrative data for the dashboard
    print("DB seeded OK")

    # ---- per-service commission rules -------------------------------------
    from sus.models import Service, Worker, Transaction
    from sus.commission import resolve_rate, split_lines, default_rate

    barber = Worker.query.filter_by(category="Barber").first()
    haircut = Service.query.filter_by(name="Classic Haircut").one()
    braid = Service.query.filter_by(name="Braiding / Weaving").one()
    print(f"rates          -> haircut {resolve_rate(barber, haircut)}% "
          f"(price {haircut.price}), braid {resolve_rate(barber, braid)}% "
          f"(price {braid.price}), shop default {default_rate()}%")
    assert resolve_rate(barber, haircut) == haircut.commission_rate
    assert haircut.commission_rate != braid.commission_rate, "services must differ"

    # a 2-line visit must pay each line at its own percentage
    lines = split_lines(barber, [haircut, braid])
    expected = round(haircut.price * haircut.commission_rate / 100) + \
               round(braid.price * braid.commission_rate / 100)
    print(f"split_lines    -> {[(s.name, r, c) for s, r, c in lines]} = {expected} RWF")
    assert sum(c for _, _, c in lines) == expected

    # a service with no percentage falls back to the worker's own rate
    haircut.commission_rate = None
    assert resolve_rate(barber, haircut) == barber.rate, "must fall back to worker rate"
    haircut.commission_rate = 50
    db.session.commit()
    print(f"fallback       -> works (blank service % -> worker {barber.rate}%)")

c = app.test_client()

# public pages
for url in ["/", "/about", "/services", "/team", "/booking", "/contact"]:
    r = c.get(url)
    print(f"{url:15} -> {r.status_code}")

# booking API
r = c.post("/api/book", json={"service_id": 1, "worker_id": "any",
                              "date": "2026-10-01", "time": "10:00",
                              "name": "Test Client", "phone": "+250 788 999 888"})
print("/api/book      ->", r.status_code, r.get_json().get("ok"))

# admin auth flow
r = c.get("/admin/", follow_redirects=False)
print("/admin/ (anon) ->", r.status_code, "(expect 302 to login)")
r = c.post("/admin/login", data={"email": "owner@suskigali.rw", "password": "admin123"})
print("login owner    ->", r.status_code)

for url in ["/admin/", "/admin/calendar", "/admin/transactions", "/admin/appointments",
            "/admin/workers", "/admin/services", "/admin/clients", "/admin/inventory",
            "/admin/expenses", "/admin/reports", "/admin/payroll", "/admin/settings",
            "/admin/my"]:
    r = c.get(url)
    print(f"{url:22} -> {r.status_code}")

r = c.get("/admin/calendar/export.csv")
print("CSV export     ->", r.status_code)

# Save a service with an explicit worker percentage, then sell it.
r = c.post("/admin/services/save", data={
    "name": "Smoke Test Cut", "category": "Barber", "price": "4000",
    "duration_minutes": "20", "description": "created by smoke_test", "commission_rate": "55",
}, follow_redirects=False)
print("service save   ->", r.status_code, "(302 expected)")

with app.app_context():
    from sus.commission import resolve_rate as _rr
    from sus.models import Service as _S, Worker as _W, Transaction as _T
    svc = _S.query.filter_by(name="Smoke Test Cut").one()
    w = _W.query.filter_by(status="active").first()
    print(f"service rate   -> {svc.commission_rate}% (expected 55.0)")
    assert svc.commission_rate == 55.0

    before = _T.query.count()
    c.post("/admin/transactions/record", data={
        "worker_id": str(w.id), "service_ids": [str(svc.id)],
        "date": "2026-10-02", "time": "11:00", "payment_method": "Cash",
    })
    after = _T.query.count()
    tx = _T.query.order_by(_T.id.desc()).first()
    print(f"record         -> transactions {before} -> {after}")
    print(f"transaction    -> amount {tx.amount}, commission {tx.commission_amount} "
          f"(expected 2200), salon {tx.salon_amount}")
    assert tx.commission_amount == 2200, tx.commission_amount
    assert tx.items[0].commission_rate == 55.0
    assert tx.salon_amount == tx.amount - tx.commission_amount

    # A blank percentage must fall back, not crash.
    r = c.post("/admin/services/save", data={
        "name": "Fallback Cut", "category": "Barber", "price": "5000",
        "duration_minutes": "20", "commission_rate": "",
    }, follow_redirects=False)
    fb = _S.query.filter_by(name="Fallback Cut").one()
    print(f"blank rate     -> {fb.commission_rate} (expected None), inherited {_rr(w, fb)}%")
    assert fb.commission_rate is None

# worker login
c.get("/admin/logout")
r = c.post("/admin/login", data={"email": "eric@suskigali.rw", "password": "eric123"})
r = c.get("/admin/my")
print("worker /admin/my ->", r.status_code)

print("SMOKE TEST DONE")
