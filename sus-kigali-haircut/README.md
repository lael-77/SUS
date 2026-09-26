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
