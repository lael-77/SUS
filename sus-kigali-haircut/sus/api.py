"""JSON API used by the public booking flow (real-time availability, Section 3.2)."""
from flask import Blueprint, jsonify, request

from .models import Service, Worker, Appointment, Setting

api_bp = Blueprint("api", __name__, url_prefix="/api")

OPEN_HOUR, CLOSE_HOUR, SLOT_MIN = 8, 20, 30


def slots_for_day():
    out = []
    for h in range(OPEN_HOUR, CLOSE_HOUR):
        for m in (0, SLOT_MIN):
            out.append(f"{h:02d}:{m:02d}")
    return out


@api_bp.route("/services")
def services():
    restrict = Setting.get("restrict_service_category", "1") == "1"
    return jsonify([{"id": s.id, "name": s.name, "category": s.category,
                     "price": s.price, "duration": s.duration_minutes}
                    for s in Service.query.filter_by(active=True).all()])


@api_bp.route("/workers")
def workers():
    category = request.args.get("category")
    q = Worker.query.filter_by(status="active")
    if category:
        q = q.filter_by(category=category)
    return jsonify([{"id": w.id, "name": w.full_name, "category": w.category,
                      "specialty": w.specialty or ""} for w in q.all()])


@api_bp.route("/availability")
def availability():
    """Free 30-min slots for a worker on a date (blocks already-booked slots)."""
    worker_id = request.args.get("worker_id")
    date = request.args.get("date")
    if not date:
        return jsonify([])
    all_slots = slots_for_day()

    if not worker_id or worker_id == "any":
        # union of every active worker's free slots
        taken_by_slot = {}
        for a in Appointment.query.filter_by(date=date)\
                .filter(Appointment.status.in_(["pending", "confirmed"])).all():
            taken_by_slot.setdefault(a.time, set()).add(a.worker_id)
        n_workers = Worker.query.filter_by(status="active").count()
        return jsonify([s for s in all_slots if len(taken_by_slot.get(s, ())) < n_workers])

    taken = {a.time for a in Appointment.query
            .filter_by(worker_id=int(worker_id), date=date)
            .filter(Appointment.status.in_(["pending", "confirmed"])).all()}
    return jsonify([s for s in all_slots if s not in taken])
