"""SUS KIGALI HAIRCUT — Database models (per documentation Section 7).

All monetary amounts are integers in RWF (Rwandan Francs).
"""
from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

WORKER_CATEGORIES = ["Barber", "Hairstylist", "Nail Technician", "Other"]
PAY_TYPES = ["commission", "fixed", "hybrid"]
PAYMENT_METHODS = ["Cash", "MTN MoMo", "Airtel Money", "Card"]
APPOINTMENT_STATUSES = ["pending", "confirmed", "completed", "cancelled", "no_show"]
PAYROLL_STATUSES = ["draft", "paid"]


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.String(20), nullable=False, default="worker")  # super_admin / manager / worker
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    worker = db.relationship("Worker", backref="user", uselist=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class Setting(db.Model):
    """Key/value store for configurable business settings (Section 5.5)."""
    __tablename__ = "settings"
    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.String(255), nullable=False)

    @staticmethod
    def get(key, default=None):
        s = Setting.query.get(key)
        return s.value if s else default

    @staticmethod
    def set(key, value):
        s = Setting.query.get(key)
        if s:
            s.value = str(value)
        else:
            db.session.add(Setting(key=key, value=str(value)))


class Worker(db.Model):
    __tablename__ = "workers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    photo = db.Column(db.String(255))  # path/URL, optional
    category = db.Column(db.String(40), nullable=False, default="Barber")
    specialty = db.Column(db.String(120))
    commission_rate = db.Column(db.Float)  # percent; None -> use shop default
    pay_type = db.Column(db.String(20), nullable=False, default="commission")
    base_salary = db.Column(db.Integer, default=0)  # for fixed / hybrid
    date_joined = db.Column(db.String(10), default=lambda: date.today().isoformat())
    status = db.Column(db.String(20), nullable=False, default="active")

    @property
    def rate(self):
        return self.commission_rate if self.commission_rate is not None \
            else float(Setting.get("default_commission_rate", 20))

    def __repr__(self):
        return f"<Worker {self.full_name} ({self.category})>"


class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Integer, nullable=False)  # RWF
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    category = db.Column(db.String(40), nullable=False, default="Barber")
    active = db.Column(db.Boolean, nullable=False, default=True)


class Client(db.Model):
    __tablename__ = "clients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120))
    preferred_worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"))
    visit_count = db.Column(db.Integer, nullable=False, default=0)
    total_spent = db.Column(db.Integer, nullable=False, default=0)
    loyalty_points = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    time = db.Column(db.String(5), nullable=False)   # HH:MM
    status = db.Column(db.String(20), nullable=False, default="pending")
    source = db.Column(db.String(20), nullable=False, default="online")  # online / walk_in
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    client = db.relationship("Client")
    worker = db.relationship("Worker")
    service = db.relationship("Service")


class TransactionItem(db.Model):
    __tablename__ = "transaction_items"
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"))
    service_name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # RWF charged for this line


class Transaction(db.Model):
    """A completed service visit. Recording it triggers commission calculation (Section 5)."""
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))
    date = db.Column(db.String(10), nullable=False, default=lambda: date.today().isoformat())
    time = db.Column(db.String(5), nullable=False, default=lambda: datetime.now().strftime("%H:%M"))
    amount = db.Column(db.Integer, nullable=False, default=0)          # gross after discount
    discount = db.Column(db.Integer, nullable=False, default=0)
    discount_reason = db.Column(db.String(255))
    tip = db.Column(db.Integer, nullable=False, default=0)             # 100% to worker
    commission_amount = db.Column(db.Integer, nullable=False, default=0)
    salon_amount = db.Column(db.Integer, nullable=False, default=0)
    payment_method = db.Column(db.String(20), nullable=False, default="Cash")
    status = db.Column(db.String(20), nullable=False, default="completed")  # completed / void
    note = db.Column(db.String(255))
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("TransactionItem", backref="transaction", cascade="all, delete-orphan")
    worker = db.relationship("Worker")
    client = db.relationship("Client")


class Payroll(db.Model):
    __tablename__ = "payroll"
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"), nullable=False)
    period_start = db.Column(db.String(10), nullable=False)
    period_end = db.Column(db.String(10), nullable=False)
    total_clients = db.Column(db.Integer, nullable=False, default=0)
    gross_revenue = db.Column(db.Integer, nullable=False, default=0)
    commission_earned = db.Column(db.Integer, nullable=False, default=0)
    bonus = db.Column(db.Integer, nullable=False, default=0)
    deductions = db.Column(db.Integer, nullable=False, default=0)
    net_pay = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="draft")
    paid_date = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    worker = db.relationship("Worker")


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(255))
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(10), nullable=False, default=lambda: date.today().isoformat())
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"))


class InventoryItem(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60))
    quantity = db.Column(db.Float, nullable=False, default=0)
    unit = db.Column(db.String(20), default="pcs")
    reorder_level = db.Column(db.Float, nullable=False, default=0)
    unit_cost = db.Column(db.Integer, nullable=False, default=0)

    @property
    def low_stock(self):
        return self.quantity <= self.reorder_level


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"))
    rating = db.Column(db.Integer, nullable=False)  # 1..5
    comment = db.Column(db.String(500))
    date = db.Column(db.String(10), nullable=False, default=lambda: date.today().isoformat())


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    clock_in = db.Column(db.String(5))
    clock_out = db.Column(db.String(5))
    status = db.Column(db.String(20), default="present")

