"""Commission & payroll engine (documentation Section 5).

Core formula:
    commission_amount = price x commission_rate (default 20%)
    salon_amount      = price x (1 - commission_rate)

Configurable rules (Settings, section 5.5):
    - commission rate per worker or shop-wide default
    - discounts: commission on amount actually paid (default) or on full price
    - tips: tracked separately, 100% to the worker
"""
from .models import Transaction, TransactionItem, db


def commission_base(gross, discount, on_discounted=True):
    """The amount commission is calculated on."""
    return gross if on_discounted else gross + discount


def compute_split(worker, gross, discount=0, tip=0, on_discounted=True):
    """Return (amount_paid, commission, salon_amount, tip) for one visit."""
    base = commission_base(gross, discount, on_discounted)
    rate = worker.rate / 100.0
    commission = round(base * rate)
    salon = gross - commission
    return gross, commission, salon, tip


def record_transaction(worker, service_ids, client=None, discount=0, discount_reason=None,
                       tip=0, payment_method="Cash", note=None, recorded_by=None,
                       date=None, time=None, on_discounted=True):
    """Create a Transaction with automatic commission calculation.

    Supports multiple services in one visit (haircut + beard trim, etc.).
    """
    from .models import Service
    services = Service.query.filter(Service.id.in_(service_ids)).all()
    gross = sum(s.price for s in services)
    amount, commission, salon, tip = compute_split(worker, gross, discount, tip, on_discounted)

    t = Transaction(
        worker_id=worker.id,
        client_id=client.id if client else None,
        amount=amount, discount=discount, discount_reason=discount_reason, tip=tip,
        commission_amount=commission, salon_amount=salon,
        payment_method=payment_method, note=note, recorded_by=recorded_by,
        date=date, time=time,
    )
    for s in services:
        t.items.append(TransactionItem(service_id=s.id, service_name=s.name, price=s.price))
    db.session.add(t)

    # Update client CRM counters + loyalty (1 point per visit, 1 per 1,000 RWF)
    if client:
        client.visit_count += 1
        client.total_spent += amount
        client.loyalty_points += 1 + amount // 1000

    return t
