"""Public website — classic heritage-barbershop frontend (documentation Section 3).

Prices shown here always come from the live service list in the database,
never hardcoded twice (Section 3.3).
"""
from flask import Blueprint, render_template, request, jsonify

from .models import (db, Setting, Service, Worker, Appointment, Client, Review)

public_bp = Blueprint("public", __name__)


def shop():
    return {
        "name": Setting.get("shop_name", "SUS KIGALI HAIRCUT"),
        "tagline": Setting.get("tagline", ""),
        "phone": Setting.get("phone", ""),
        "whatsapp": Setting.get("whatsapp", ""),
        "address": Setting.get("address", ""),
        "hours": Setting.get("hours", ""),
    }


@public_bp.app_context_processor
def inject_shop():
    return {"shop": shop()}


@public_bp.route("/")
def home():
    featured = Service.query.filter_by(active=True).order_by(Service.id).limit(6).all()
    team = Worker.query.filter_by(status="active").order_by(Worker.id).limit(3).all()
    reviews = Review.query.order_by(Review.id.desc()).limit(3).all()
    return render_template("home.html", featured=featured, team=team, reviews=reviews)


@public_bp.route("/about")
def about():
    return render_template("about.html")


@public_bp.route("/services")
def services():
    grouped = {}
    for s in Service.query.filter_by(active=True).order_by(Service.category, Service.price).all():
        grouped.setdefault(s.category, []).append(s)
    return render_template("services.html", grouped=grouped)


@public_bp.route("/team")
def team():
    grouped = {}
    for w in Worker.query.filter_by(status="active").order_by(Worker.id).all():
        grouped.setdefault(w.category, []).append(w)
    return render_template("team.html", grouped=grouped)


@public_bp.route("/booking")
def booking():
    services = Service.query.filter_by(active=True).order_by(Service.category, Service.name).all()
    return render_template("booking.html", services=services)


@public_bp.route("/contact")
def contact():
    return render_template("contact.html")


@public_bp.route("/api/book", methods=["POST"])
def api_book():
    """Booking form submit: service -> worker -> date/time -> name + phone."""
    data = request.get_json() or {}
    try:
        service = Service.query.get(int(data.get("service_id")))
        worker_id = data.get("worker_id")
        date, time = data.get("date"), data.get("time")
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()
        if not (service and date and time and name and phone):
            return jsonify(ok=False, error="Please fill in every field.")

        # category restriction (configurable, Section 5.5)
        if worker_id in (None, "", "any"):
            worker = (Worker.query.filter_by(status="active", category=service.category).first())
            if not worker:
                return jsonify(ok=False, error="No worker available for this service.")
        else:
            worker = Worker.query.get(int(worker_id))
            if not worker or worker.status != "active":
                return jsonify(ok=False, error="Selected worker is not available.")
            if Setting.get("restrict_service_category", "1") == "1" and \
                    worker.category != service.category:
                return jsonify(ok=False, error="That worker does not perform this service.")

        clash = Appointment.query.filter_by(worker_id=worker.id, date=date, time=time)\
            .filter(Appointment.status.in_(["pending", "confirmed"])).first()
        if clash:
            return jsonify(ok=False, error="Sorry, that slot was just taken. Pick another time.")

        client = Client.query.filter_by(phone=phone).first()
        if not client:
            client = Client(name=name, phone=phone)
            db.session.add(client)
        client.preferred_worker_id = worker.id

        appt = Appointment(client=client, worker_id=worker.id, service_id=service.id,
                           date=date, time=time, status="confirmed", source="online")
        db.session.add(appt)
        db.session.commit()
        return jsonify(ok=True,
                       message=f"Booking confirmed! {name}, you're booked with {worker.full_name} "
                               f"on {date} at {time} for {service.name}. "
                               f"A confirmation will be sent to {phone}.")
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Invalid booking details.")
