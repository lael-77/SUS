"""Commission & payroll engine (documentation Section 5).

Commission is decided **per service**, because the shop does not make the same
margin on every treatment. The rule, in order of precedence:

    1. the service's own ``commission_rate``      (Admin > Services & Prices)
    2. the worker's ``commission_rate``           (Admin > Workers — e.g. an
                                                   apprentice on a lower share)
    3. the shop-wide ``default_commission_rate``  (Admin > Settings)

A visit that includes several services accrues each line at its own
percentage and the lines are summed. Example: a 10,000 RWF haircut at 50 %
plus a 5,000 RWF beard trim at 30 % pays 5,000 + 1,500 = 6,500 RWF.

Other configurable rules (Settings, section 5.5):
    - discounts: commission on the amount actually collected (default) or on
      the full price; a multi-service discount is spread across the lines in
      proportion to their price
    - tips: tracked separately, 100 % to the worker
"""
from .models import Transaction, TransactionItem, Setting, db


def default_rate():
    """The shop-wide fallback percentage, as a float."""
    try:
        return float(Setting.get("default_commission_rate", 20))
    except (TypeError, ValueError):
        return 20.0


def resolve_rate(worker, service=None):
    """The commission percentage that applies to this worker/service pair."""
    rate = getattr(service, "commission_rate", None)
    if rate is not None:
        return float(rate)
    if worker is not None:
        return float(worker.rate)
    return default_rate()


def commission_base(gross, discount, on_discounted=True):
    """The amount commission is calculated on."""
    return gross if on_discounted else gross + discount


def _as_list(services):
    """Accept a Service, a list/tuple of them, or a SQLAlchemy query/result."""
    if hasattr(services, "all"):
        services = services.all()
    elif hasattr(services, "price"):
        services = [services]
    return list(services)


def split_lines(worker, services, discount=0, on_discounted=True):
    """Per-service breakdown: ``[(service, rate_percent, commission), ...]``."""
    services = _as_list(services)
    gross = sum(s.price for s in services)
    base_total = commission_base(gross, discount, on_discounted)
    lines = []
    for s in services:
        share = (s.price / gross) if gross else 0.0
        rate = resolve_rate(worker, s)
        lines.append((s, rate, round(base_total * share * rate / 100.0)))
    return lines


def compute_split(worker, services, discount=0, tip=0, on_discounted=True):
    """Return ``(amount, commission, salon_amount, tip)`` for one visit."""
    services = _as_list(services)
    gross = sum(s.price for s in services)
    commission = sum(line[2] for line in split_lines(worker, services, discount, on_discounted))
    return gross, commission, gross - commission, tip


def record_transaction(worker, service_ids, client=None, discount=0, discount_reason=None,
                       tip=0, payment_method="Cash", note=None, recorded_by=None,
                       date=None, time=None, on_discounted=True):
    """Create a Transaction with automatic per-service commission calculation.

    Supports multiple services in one visit (haircut + beard trim, etc.).
    """
    from .models import Service
    services = Service.query.filter(Service.id.in_(service_ids))\
        .order_by(Service.id).all()
    lines = split_lines(worker, services, discount, on_discounted)

    gross = sum(s.price for s in services)
    commission = sum(line[2] for line in lines)
    amount, salon = gross, gross - commission

    t = Transaction(
        worker_id=worker.id,
        client_id=client.id if client else None,
        amount=amount, discount=discount, discount_reason=discount_reason, tip=tip,
        commission_amount=commission, salon_amount=salon,
        payment_method=payment_method, note=note, recorded_by=recorded_by,
        date=date, time=time,
    )
    # Each line keeps the percentage it was paid at, so an old receipt stays
    # correct even after the service's percentage is changed later.
    for s, rate, line_commission in lines:
        t.items.append(TransactionItem(service_id=s.id, service_name=s.name,
                                       price=s.price, commission_rate=rate,
                                       commission_amount=line_commission))
    db.session.add(t)

    # Update client CRM counters + loyalty (1 point per visit, 1 per 1,000 RWF)
    if client:
        client.visit_count += 1
        client.total_spent += amount
        client.loyalty_points += 1 + amount // 1000

    return t
