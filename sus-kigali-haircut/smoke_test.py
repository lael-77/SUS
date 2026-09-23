"""Smoke test: seed the DB and hit every route with Flask's test client."""
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sus import create_app, db, seed_data

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    seed_data()
    print("DB seeded OK")

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

# worker login
c.get("/admin/logout")
r = c.post("/admin/login", data={"email": "eric@suskigali.rw", "password": "eric123"})
r = c.get("/admin/my")
print("worker /admin/my ->", r.status_code)

print("SMOKE TEST DONE")
