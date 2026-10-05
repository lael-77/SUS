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
python run.py            # create/upgrade the DB, bootstrap it, serve on http://127.0.0.1:5000
```

### Commands

| Command                | What it does                                                                  |
|------------------------|-------------------------------------------------------------------------------|
| `python run.py`        | Create/upgrade the database, then serve on `http://127.0.0.1:5000`             |
| `python run.py init`   | Only create/upgrade the database and the owner login, then exit                |
| `python run.py clean`  | **Drop every table** and re-create an empty shop (settings + owner only)       |
| `python run.py reseed` | Rebuild the database with the illustrative demo dataset                        |
| `python smoke_test.py` | End-to-end check of every route plus the commission maths (own database)        |

`clean` and `reseed` are destructive by design — that is what "wipe the seed
data" means. Both now finish and exit instead of leaving a server running behind
them.

### Accounts

The bootstrap always creates the owner login. The other three only exist when you
run `reseed` — they are demo staff.

| Role         | Login (email)             | Password    | Created by  |
|--------------|---------------------------|-------------|-------------|
| Super admin  | `owner@suskigali.rw`      | `admin123`  | bootstrap   |
| Manager      | `manager@suskigali.rw`    | `manager123`| `reseed`    |
| Worker       | `eric@suskigali.rw`       | `eric123`   | `reseed`    |
| Worker       | `divine@suskigali.rw`     | `divine123` | `reseed`    |

Change the owner password and the shop details under **Admin › Settings** before
going live.

## Structure

```
run.py                  entry point — `run.py [init|clean|reseed]`
config.py               app configuration + the shop's contact details
smoke_test.py           end-to-end test of every route and the commission maths
sus/
  __init__.py           app factory, blueprint registration
  models.py             ORM models (workers, services, transactions, ...)
  schema.py             additive ALTER TABLE upgrades for existing databases
  auth.py               login/logout, role-based access
  public.py             public website + /api/book
  admin.py              owner/super-admin dashboard + worker portal
  api.py                JSON endpoints (workers, availability)
  commission.py         commission engine — per-service rates (Section 5)
  seed.py               bootstrap (settings + owner) and the demo dataset
  templates/            Jinja2 templates (public + admin)
  static/css            theme.css (design tokens) → public.css / admin.css
  static/js             site.js (public polish) + booking.js (booking flow)
```

## Design system — "Pole & Blade"

The website and the dashboard share one set of design tokens, so the register at
the counter and the public site read as a single product.

```
static/css/theme.css    design tokens + shared primitives (reset, layout,
                        type helpers, buttons, badges, tables, form controls,
                        scroll-reveal). Loaded by both surfaces.
static/css/public.css   public-site components only
static/css/admin.css    dashboard components only
static/css/fonts.css    @font-face declarations for the self-hosted fonts
static/js/site.js       sticky-header shadow, mobile-nav close, scroll reveals
```

- **Brand colours** are sampled from the shop logo: gold `#FED700`, red `#EE1C25`,
  blue `#0F74BC`, ink `#0B0B0C`. All colours, spacing, radii, type sizes,
  shadows and motion durations are CSS custom properties in `theme.css` — change
  a token there and both surfaces follow.
- **Accessibility:** brand gold is a *fill*, not body text on light surfaces. Gold
  text on paper uses `--gold-ink` (`#7A5E00`, 6.2:1 against the cream background);
  pure `--gold` is reserved for fills, rules and dark surfaces. Every interactive
  element has a visible `:focus-visible` ring, there is a skip link on the public
  site, and all motion is disabled under `prefers-reduced-motion`.
- **Scroll reveals** are opt-in per element with `data-reveal` (and
  `data-reveal-delay="1…5"` for stagger); `site.js` adds `.is-visible` via
  `IntersectionObserver` and falls back to showing everything if the API is
  missing.
- **No JavaScript is required** for any page to work. `site.js` and the inline
  admin helpers only add polish; navigation, links and the booking flow all
  function without it.

Assets are documented in [`CREDITS.md`](CREDITS.md) — brand artwork, font licences
and the Unsplash photo IDs.
```

## Business rules (from documentation)

- **Commission is set per service.** Every service carries its own worker
  percentage, because the shop does not make the same margin on a 10,000 RWF
  haircut as on a 20,000 RWF braiding job. For each sale the engine looks at, in
  order:

  1. the **service's own percentage** — `Admin › Services & Prices`
  2. otherwise the **worker's own rate** — `Admin › Workers` (e.g. an apprentice)
  3. otherwise the **shop default** — `Admin › Settings`

  A visit with several services accrues each line at its own percentage and the
  lines are summed. A discount is spread across the lines in proportion to their
  price. Tips are tracked separately and go 100 % to the worker. Each
  `transaction_item` stores the percentage and the amount it was paid at, so an
  old receipt stays correct after a rate is changed.
- Payroll summarizes commission, tips, bonuses and deductions per worker per period.
- Income calendar color-codes each day's total revenue.
- Every price on the public site comes from the live database — nothing is
  hardcoded twice.
- Optional restriction: workers may only be booked for services in their own
  category (toggle in Settings).

## Contact details and branding

The shop name, phone number and WhatsApp number live in **one place**:
`config.py`.

```python
SHOP_NAME      = "SUS Kigali Haircut"
SHOP_PHONE     = "+250 785 998 860"    # shown to people
SHOP_PHONE_TEL = "+250785998860"       # what href="tel:..." uses
SHOP_WHATSAPP  = "250795410781"        # digits only, for https://wa.me/...
```

Those values are written into the `settings` table on first run and used as the
fallback everywhere — the top contact strip, the header wordmark, the footer, the
sticky mobile bar and every `tel:` / `wa.me` link. Nothing is hardcoded inside a
template, so editing `config.py` and running `python run.py init` re-brands the
whole site. Once a row exists in the database, **Admin › Settings** wins.

## Database

The app talks to whichever database the environment points at. `config.py`
resolves it in this order:

1. **`DATABASE_URL` or `POSTGRES_URL`** — a hosted Postgres.
2. **`VERCEL` set, but no connection string** — SQLite under `/tmp`, because
   serverless filesystems are read-only everywhere else.
3. **Anything else** — the SQLite file `sus_kigali.db` next to `config.py`.

Whichever engine wins, the same schema is created on first import of `run.py`.

### This project — Neon Postgres on Vercel

The live site runs on Vercel with a Neon Postgres database attached to it. To
work against that same database from this machine:

```bash
vercel link --yes --project <project-name>
vercel env pull .env.pulled --environment=production
```

Copy the `POSTGRES_URL` value into `sus-kigali-haircut/.env` as `DATABASE_URL`,
and add a `SECRET_KEY`:

```
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require&channel_binding=require
SECRET_KEY=<64 hex characters>
```

`.env` is gitignored — never commit it. `config.py` loads it with
`os.environ.setdefault()`, so a real environment variable always beats the file.
Delete `.env` (or blank out `DATABASE_URL`) to drop back to SQLite.

Then `python run.py` creates the schema and bootstraps the settings rows and the
owner login the first time it runs. Nothing else is required.

> **Note:** `smoke_test.py` always uses a throwaway SQLite file in the system
> temp directory and refuses to start if it ever finds itself on a real server,
> so it is safe to run while `.env` points at production.

### Local development — SQLite

With no `.env` the app uses `sus_kigali.db`, a SQLite file next to `config.py`.
Nothing to install, nothing to configure.

### Production / Vercel — Postgres

SQLite will not survive on Vercel: the filesystem is read-only apart from `/tmp`,
and `/tmp` is wiped between invocations, so the data would disappear. Use a
hosted Postgres — Vercel Postgres, Neon, Supabase and Railway all work.

1. **Provision the database.** In the Vercel dashboard open the project →
   *Storage* → *Create Database* → *Postgres*, or attach a Neon database through
   the *Neon* integration. Either way you end up with a connection string.

2. **Expose the connection string.** Vercel Postgres and the Neon integration
   set `POSTGRES_URL` automatically; the app also accepts `DATABASE_URL`. Add it
   to the project's environment variables if your provider uses another name:

   ```
   DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
   ```

   Both `postgres://` and `postgresql://` are accepted —
   `config._database_settings()` rewrites them to include an explicit driver
   name, which SQLAlchemy 2.x requires.

   It picks `postgresql+psycopg` when psycopg is importable (the Linux container
   on Vercel) and falls back to `postgresql+pg8000` otherwise. pg8000 is pure
   Python, so it still works on Windows machines whose Application Control policy
   blocks psycopg's compiled `pq` extension. The only visible difference is that
   pg8000 cannot read libpq's `sslmode` / `channel_binding` query parameters, so
   for that driver the query string is dropped and a real TLS context is passed
   instead — connections are still encrypted.


3. **Install the drivers.** Both are already in `requirements.txt` —
   `psycopg[binary]` for the Vercel container and `pg8000` as the portable
   fallback:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. **Create the schema.** The app does it on the first request. `run.py` calls
   `db.create_all()`, then `sus/schema.py::ensure_schema()` adds any column a
   newer version introduced (so an existing database upgrades in place without
   Alembic), then `sus/seed.py::seed_data()` writes the settings rows and the
   owner login. Nothing else is needed.

5. **Seed real data.** Sign in at `/admin/login` as `owner@suskigali.rw` /
   `admin123`, change the password, then add your services, workers and clients
   from the dashboard. Do **not** run `python run.py reseed` against production —
   that loads demo data. `reseed` and `clean` only make sense locally.

6. **Keep the session secret private.** Set `SECRET_KEY` to a long random string
   in the environment variables; the built-in default is for local development
   only:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

7. **Migrating an existing SQLite file to Postgres.** Take a maintenance window
   and back up `sus_kigali.db` first, then:

   ```bash
   # point the app at Postgres and let it build the schema + bootstrap rows
   $env:DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"
   python run.py init
   ```

   The schema is identical on both engines, so any row-copy tool works:
   `pandas.DataFrame.to_sql`, SQLAlchemy's `Table.insert()`, or a short script
   that reads with `sqlite3` and writes through the app's own `db.session`.
   Insert parents before children — `users` → `workers` / `clients` /
   `transactions` → `transaction_items`, and `workers` / `clients` before
   `appointments`, `payroll`, `reviews` and `attendance` — so the foreign keys
   resolve. Verify the dashboard, then set `DATABASE_URL` in Vercel and redeploy.

## Notes

- Amounts are in RWF (Rwandan Francs) and are stored as whole numbers.
- Deleting `sus_kigali.db` is the quickest local reset; `python run.py clean`
  does the same thing without touching the file by hand.
- `python run.py clean` keeps only the settings rows and the owner login, so the
  site is immediately usable after a wipe — just add your services and staff.
