# SUS KIGALI HAIRCUT — Shop Management System

A complete barbershop management system for **SUS KIGALI HAIRCUT** (Kigali, Rwanda),
built from scratch per the project documentation:

- **Public heritage-barbershop website** — home, about, services, team, contact,
  and a real-time online booking flow (service → worker → date → live 30-min
  slot availability → name + phone → confirmed).
- **Admin dashboard** (`/admin`) — owner/super-admin login, daily transactions,
  workers & clients, services & pricing, appointments, inventory, expenses,
  payroll (commission engine), income calendar heatmap, reports, settings.
- **Worker self-service portal** (`/admin/my`) — each worker sees only their own
  daily transactions, can add tips, and views their income & payroll history.

## Tech

- Python 3 / Flask + Flask-SQLAlchemy (SQLite by default)
- Jinja2 templates, vanilla JS/CSS (no build step)

## Quick start

```bash
cd sus-kigali-haircut
python -m pip install -r requirements.txt
python run.py            # creates the DB, seeds demo data, serves on http://127.0.0.1:5000
```

Default accounts (change them after first login under **Settings**):

| Role         | Login (email)             | Password    |
|--------------|---------------------------|-------------|
| Super admin  | `owner@suskigali.rw`      | `admin123`  |
| Manager      | `manager@suskigali.rw`    | `manager123`|
| Worker       | `eric@suskigali.rw`       | `eric123`   |
| Worker       | `divine@suskigali.rw`     | `divine123` |

## Structure

```
run.py                  entry point (init DB, seed, run)
config.py               app configuration
sus/
  __init__.py           app factory, blueprint registration
  models.py             ORM models (workers, services, transactions, ...)
  auth.py               login/logout, role-based access
  public.py             public website + /api/book
  admin.py              owner/super-admin dashboard + worker portal
  api.py                JSON endpoints (workers, availability)
  commission.py         commission engine (Section 4 payroll rules)
  seed.py               demo data
  templates/            Jinja2 templates (public + admin)
  static/css|js         styling & booking logic
smoke_test.py           end-to-end test of every route (run with app up)
```

## Business rules (from documentation)

- Commission is computed per transaction from the service price and the
  worker's commission rate; payroll summarizes per worker per month.
- Income calendar color-codes each day's total revenue.
- Every price on the public site comes from the live database — nothing is
  hardcoded twice.
- Optional restriction: workers may only be booked for services in their own
  category (toggle in Settings).

## Notes

- Data lives in `sus_kigali.db` (auto-created). Delete it to reset to seed data.
- Amounts are in RWF (Rwandan Francs).
