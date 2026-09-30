"""Database bootstrap and optional demo data.

Two clearly separated jobs live here:

``seed_data()``   BOOTSTRAP. Guarantees the shop settings rows and one
                  super-admin login exist so a brand-new installation is
                  usable straight away. It runs on every start, never
                  overwrites a value that is already stored, and creates
                  **no demo business data**.
``seed_demo()``   The full illustrative dataset (staff, service menu, sales
                  history, charts) for exploring the dashboard: run
                  ``python run.py reseed``.
``wipe_data()``   Drops every table and re-bootstraps — a clean, empty shop:
                  run ``python run.py clean``.

Logins created by the bootstrap / demo data:
    owner@suskigali.rw     / admin123   (Super Admin / Owner)
    manager@suskigali.rw   / manager123 (Manager — demo data only)
    eric@suskigali.rw      / eric123    (Worker login, Barber — demo only)
    divine@suskigali.rw    / divine123  (Worker login, Hairstylist — demo only)
"""
import random
from datetime import date, timedelta

from config import SHOP_NAME, SHOP_PHONE, SHOP_WHATSAPP
from .models import (db, User, Setting, Worker, Service, Client, Appointment,
                     Expense, InventoryItem, Review)
from .commission import record_transaction

random.seed(42)  # deterministic demo data

OWNER_EMAIL = "owner@suskigali.rw"
OWNER_PASSWORD = "admin123"

DEFAULT_SETTINGS = {
    "shop_name": SHOP_NAME,
    "tagline": "Where Kigali comes for a sharp cut.",
    "phone": SHOP_PHONE,
    "whatsapp": SHOP_WHATSAPP,
    "address": "KN 4 Ave, Kigali City Centre, Rwanda",
    "hours": "Mon-Sat 08:00 - 20:00, Sun 09:00 - 17:00",
    "currency": "RWF",
    "default_commission_rate": "20",   # only used when a service/worker has none
    "commission_on_discounted": "1",   # commission on the amount actually paid
    "restrict_service_category": "1",  # services locked to matching category
    "pay_period": "monthly",           # daily / weekly / bi-weekly / monthly
    "loyalty_visits_for_reward": "10",
}

# Contact numbers that shipped in early builds. They are placeholders, so if we
# still find one in the database we replace it with the real number from
# config.py — but a number the owner set themselves is never touched.
_PLACEHOLDER_PHONES = {"", None, "+250 788 123 456", "+250788123456", "250788123456"}

# Demo service menu: (name, description, price, minutes, category, worker %).
# The percentage is what the person performing the service keeps — services are
# deliberately NOT all the same. See sus/commission.py for the precedence rule.
DEMO_SERVICES = [
    ("Classic Haircut", "Sharp cut, hot towel finish", 10000, 30, "Barber", 50),
    ("Beard Trim", "Line-up & sculpt", 5000, 15, "Barber", 40),
    ("Haircut + Beard Combo", "The full package", 13000, 45, "Barber", 50),
    ("Kids Haircut", "Under 12, patient & gentle", 7000, 30, "Barber", 45),
    ("Hair Coloring / Dye", "Full colour service", 15000, 90, "Barber", 35),
    ("Braiding / Weaving", "Installation included", 20000, 180, "Hairstylist", 45),
    ("Hair Treatment", "Repair & moisture therapy", 12000, 60, "Hairstylist", 40),
    ("Blow-dry & Styling", "Event-ready finish", 10000, 45, "Hairstylist", 40),
    ("Manicure", "Shape, buff & polish", 6000, 40, "Nail Technician", 35),
    ("Pedicure", "Soak, scrub & polish", 8000, 50, "Nail Technician", 35),
    ("Gel Full Set", "Long-lasting gel nails", 15000, 75, "Nail Technician", 30),
]

CAT_SERVICE = {}  # category -> [service names], derived from DEMO_SERVICES
for _spec in DEMO_SERVICES:
    CAT_SERVICE.setdefault(_spec[4], []).append(_spec[0])


# --------------------------------------------------------------------------- #
#  Bootstrap — runs on every start                                             #
# --------------------------------------------------------------------------- #
def seed_data():
    """Make the app usable: shop settings + one owner login, nothing else."""
    for key, value in DEFAULT_SETTINGS.items():
        if Setting.query.get(key) is None:
            db.session.add(Setting(key=key, value=str(value)))

    if not User.query.first():
        owner = User(name="Salon Owner", email=OWNER_EMAIL, role="super_admin")
        owner.set_password(OWNER_PASSWORD)
        db.session.add(owner)

    db.session.commit()
    sync_contact_details()


def sync_contact_details():
    """Replace placeholder contact numbers with the real ones in ``config.py``.

    Anything that is not a known placeholder is left exactly as it is, so this
    never fights with a number the owner typed into Admin > Settings.
    Returns the list of setting keys it changed.
    """
    updated = []
    for key, value in (("phone", SHOP_PHONE), ("whatsapp", SHOP_WHATSAPP)):
        if Setting.get(key) in _PLACEHOLDER_PHONES:
            Setting.set(key, value)
            updated.append(key)
    if updated:
        db.session.commit()
    return updated


def wipe_data():
    """Drop every table and re-create an empty shop (settings + owner only)."""
    db.drop_all()
    db.create_all()
    seed_data()


# --------------------------------------------------------------------------- #
#  Demo data — `python run.py reseed`                                           #
# --------------------------------------------------------------------------- #
def seed_demo():
    """Build the full illustrative dataset. No-op if real data already exists."""
    if Service.query.first() or Worker.query.first():
        return  # never mix demo rows into a shop that already has real data

    seed_data()
    owner = User.query.filter_by(email=OWNER_EMAIL).first()

    # ---- Extra users for the demo (bootstrap already made the owner) ----
    manager = User(name="Aline Uwase", email="manager@suskigali.rw", role="manager")
    manager.set_password("manager123")
    db.session.add(manager)

    # ---- Workers (all categories treated the same way) ----
    worker_specs = [
        ("Eric Nshimiyimana", "Barber", "Fades & classic cuts", 8, "eric@suskigali.rw", "eric123", None),
        ("Didier Mugisha", "Barber", "Beard sculpting", 5, None, None, None),
        ("Patrick Habimana", "Barber", "Kids haircuts", 2, None, None, 15),   # apprentice at 15%
        ("Divine Ingabire", "Hairstylist", "Braiding & weaving", 6, "divine@suskigali.rw", "divine123", 25),
        ("Clarisse Mukamana", "Hairstylist", "Treatments & styling", 3, None, None, None),
        ("Josiane Nyirahabimana", "Nail Technician", "Manicure & pedicure", 4, None, None, None),
    ]
    workers = []
    for name, cat, spec, years, email, pw, rate in worker_specs:
        w_user = None
        if email:
            w_user = User(name=name, email=email, role="worker")
            w_user.set_password(pw)
            db.session.add(w_user)
        w = Worker(full_name=name, phone=f"+250 78{random.randint(1000000, 9999999)}",
                   category=cat, specialty=spec, commission_rate=rate, pay_type="commission",
                   date_joined=(date.today() - timedelta(days=365 * years)).isoformat(),
                   user=w_user)
        db.session.add(w)
        workers.append(w)

    # ---- Services (illustrative menu; the % is what the worker keeps) ----
    services = {}
    for name, desc, price, dur, cat, rate in DEMO_SERVICES:
        s = Service(name=name, description=desc, price=price, duration_minutes=dur,
                    category=cat, commission_rate=rate)
        db.session.add(s)
        services[name] = s

    # ---- Clients ----
    client_names = [
        ("Jean Bosco", "+250 788 200 111"), ("Emmanuel K.", "+250 788 200 112"),
        ("Sandrine U.", "+250 788 200 113"), ("Aline M.", "+250 788 200 114"),
        ("Thierry N.", "+250 788 200 115"), ("Diane S.", "+250 788 200 116"),
        ("Fabrice H.", "+250 788 200 117"), ("Chantal N.", "+250 788 200 118"),
    ]
    clients = []
    for name, phone in client_names:
        c = Client(name=name, phone=phone)
        db.session.add(c)
        clients.append(c)

    # ---- Transactions across the last 30 days (so charts/calendar have data) ----
    methods = ["Cash", "Cash", "Cash", "MTN MoMo", "Airtel Money", "Card"]
    today = date.today()
    for d in range(30, -1, -1):
        day = today - timedelta(days=d)
        for _ in range(random.randint(4, 10)):
            w = random.choice(workers)
            picks = random.sample(CAT_SERVICE[w.category], k=random.randint(1, 2))
            client = random.choice(clients)
            discount = random.choice([0, 0, 0, 0, 1000])
            tip = random.choice([0, 0, 0, 500, 1000])
            record_transaction(w, [services[p].id for p in picks], client=client,
                               discount=discount, tip=tip,
                               payment_method=random.choice(methods),
                               date=day.isoformat(),
                               time=f"{random.randint(8, 19):02d}:{random.choice(['00', '30'])}",
                               recorded_by=owner.id)
    db.session.commit()  # assign IDs before creating appointments

    # ---- Upcoming appointments ----
    for d in range(0, 4):
        day = today + timedelta(days=d)
        for _ in range(random.randint(1, 4)):
            w = random.choice(workers)
            sname = random.choice(CAT_SERVICE[w.category])
            c = random.choice(clients)
            db.session.add(Appointment(client_id=c.id, worker_id=w.id,
                                       service_id=services[sname].id, date=day.isoformat(),
                                       time=f"{random.randint(8, 18):02d}:{random.choice(['00', '30'])}",
                                       status="confirmed", source=random.choice(["online", "walk_in"])))

    # ---- Inventory ----
    inventory = [
        ("Clipper blades", "Tools", 12, "pcs", 5, 8000),
        ("Shampoo 1L", "Products", 4, "bottle", 5, 9000),
        ("Conditioner 1L", "Products", 3, "bottle", 5, 9500),
        ("Hair pomade", "Products", 18, "jar", 10, 4500),
        ("Towels", "Supplies", 30, "pcs", 15, 3000),
        ("Braiding hair packs", "Products", 8, "pack", 10, 12000),
        ("Nail polish set", "Products", 6, "set", 4, 15000),
        ("Barbicide disinfectant", "Supplies", 2, "bottle", 3, 11000),
    ]
    for item in inventory:
        db.session.add(InventoryItem(item_name=item[0], category=item[1], quantity=item[2],
                                     unit=item[3], reorder_level=item[4], unit_cost=item[5]))

    # ---- Expenses ----
    for d in range(30, 0, -6):
        day = (today - timedelta(days=d)).isoformat()
        db.session.add(Expense(category="Rent", description="Shop rent", amount=250000, date=day, recorded_by=owner.id))
        db.session.add(Expense(category="Utilities", description="Electricity & water", amount=random.randint(30000, 60000), date=day, recorded_by=owner.id))
        db.session.add(Expense(category="Restocking", description="Product restock", amount=random.randint(20000, 80000), date=day, recorded_by=owner.id))

    # ---- Reviews ----
    comments = ["Best fade in Kigali!", "Very professional service.", "My braids lasted weeks.",
                "Clean shop, friendly staff.", "Perfect manicure, will return."]
    for _ in range(8):
        db.session.add(Review(client_id=random.choice(clients).id, worker_id=random.choice(workers).id,
                              rating=random.choice([4, 5, 5, 5]), comment=random.choice(comments)))

    db.session.commit()
