"""Admin dashboard — the operational brain of the business (documentation Section 4).

Role access:
    super_admin : everything
    manager     : day-to-day operations (workers, services, transactions, clients,
                  appointments, inventory, expenses, calendar, reports)
    worker      : /admin/my only (own schedule, own clients, own earnings)
"""
from datetime import date, timedelta
from collections import defaultdict

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, jsonify)
from sqlalchemy import func

from .auth import current_user, login_required, role_required
from .models import (db, User, Setting, Worker, Service, Client, Appointment,
                     Transaction, TransactionItem, Payroll, Expense,
                     InventoryItem, Review)
from .commission import record_transaction

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _setting(key, default):
    return Setting.get(key, default)


# ---------------------------------------------------------------- login/logout
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        u = User.query.filter(func.lower(User.email) == email).first()
        if u and u.status == "active" and u.check_password(pw):
            session["user_id"] = u.id
            session["role"] = u.role
            dest = request.args.get("next")
            if dest and dest.startswith("/"):
                return redirect(dest)
            if u.role == "worker":
                return redirect(url_for("admin.my"))
            return redirect(url_for("admin.overview"))
        return render_template("admin/login.html", error="Invalid email or password."), 401
    return render_template("admin/login.html", error=None)


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("public.home"))


# ---------------------------------------------------------------- overview (4.2a)
@admin_bp.route("/")
@login_required
def overview():
    u = current_user()
    if u.role == "worker":
        return redirect(url_for("admin.my"))
    today = date.today().isoformat()

    day_tx = Transaction.query.filter_by(date=today, status="completed").all()
    today_revenue = sum(t.amount for t in day_tx)
    clients_today = len(day_tx)
    top_today = None
    if day_tx:
        per_worker = defaultdict(int)
        for t in day_tx:
            per_worker[t.worker.full_name] += t.amount
        top_today = max(per_worker.items(), key=lambda kv: kv[1])

    # 14-day revenue trend for the bar chart
    trend = []
    for d in range(13, -1, -1):
        day = (date.today() - timedelta(days=d)).isoformat()
        tx = Transaction.query.filter_by(date=day, status="completed").all()
        trend.append({"day": day, "revenue": sum(t.amount for t in tx),
                      "commission": sum(t.commission_amount for t in tx)})

    upcoming = (Appointment.query
                .filter(Appointment.status.in_(["pending", "confirmed"]),
                        Appointment.date >= today)
                .order_by(Appointment.date, Appointment.time).limit(12).all())
    low_stock = [i for i in InventoryItem.query.all() if i.low_stock]

    # month-to-date totals
    month_start = today[:8] + "01"
    month_tx = Transaction.query.filter(Transaction.date >= month_start,
                                        Transaction.status == "completed").all()
    month_revenue = sum(t.amount for t in month_tx)
    month_commission = sum(t.commission_amount for t in month_tx)
    month_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0))\
        .filter(Expense.date >= month_start).scalar()

    return render_template("admin/overview.html", u=u,
                           today_revenue=today_revenue, clients_today=clients_today,
                           appts_today=len([a for a in upcoming if a.date == today]),
                           top_today=top_today, trend=trend, upcoming=upcoming,
                           low_stock=low_stock, month_revenue=month_revenue,
                           month_commission=month_commission,
                           month_profit=month_revenue - month_commission - month_expenses)


# ---------------------------------------------------------------- workers (4.2b)
@admin_bp.route("/workers")
@role_required("super_admin", "manager")
def workers():
    category = request.args.get("category")
    q = Worker.query.order_by(Worker.status, Worker.full_name)
    if category:
        q = q.filter_by(category=category)

    month_start = date.today().isoformat()[:8] + "01"
    perf = {}
    for w in q.all():
        tx = Transaction.query.filter_by(worker_id=w.id, status="completed")\
            .filter(Transaction.date >= month_start).all()
        perf[w.id] = {"clients": len(tx),
                      "revenue": sum(t.amount for t in tx),
                      "commission": sum(t.commission_amount for t in tx)}
    return render_template("admin/workers.html", workers=q.all(), perf=perf,
                           categories=["Barber", "Hairstylist", "Nail Technician", "Other"],
                           category=category, default_rate=_setting("default_commission_rate", 20))


@admin_bp.route("/workers/save", methods=["POST"])
@role_required("super_admin", "manager")
def worker_save():
    f = request.form
    wid = f.get("id")
    rate = f.get("commission_rate", "").strip()
    w = Worker.query.get(int(wid)) if wid else Worker()
    w.full_name = f.get("full_name", "").strip()
    w.phone = f.get("phone", "").strip() or None
    w.category = f.get("category", "Barber")
    w.specialty = f.get("specialty", "").strip() or None
    w.pay_type = f.get("pay_type", "commission")
    w.base_salary = int(f.get("base_salary") or 0)
    w.commission_rate = float(rate) if rate else None
    w.status = f.get("status", "active")

    # optional login for the worker
    email = f.get("email", "").strip()
    if email:
        if not w.user:
            w.user = User(name=w.full_name, email=email, role="worker")
        else:
            w.user.email = email
            w.user.name = w.full_name
        pw = f.get("password", "")
        if pw:
            w.user.set_password(pw)
    db.session.add(w)
    db.session.commit()
    return redirect(url_for("admin.workers"))


@admin_bp.route("/workers/<int:wid>/toggle", methods=["POST"])
@role_required("super_admin", "manager")
def worker_toggle(wid):
    w = Worker.query.get_or_404(wid)
    w.status = "inactive" if w.status == "active" else "active"
    db.session.commit()
    return redirect(url_for("admin.workers"))


# ---------------------------------------------------------------- services (4.2c)
@admin_bp.route("/services")
@role_required("super_admin", "manager")
def services():
    grouped = defaultdict(list)
    for s in Service.query.order_by(Service.category, Service.name).all():
        grouped[s.category].append(s)
    return render_template("admin/services.html", grouped=grouped,
                           categories=["Barber", "Hairstylist", "Nail Technician", "Other"])


@admin_bp.route("/services/save", methods=["POST"])
@role_required("super_admin", "manager")
def service_save():
    f = request.form
    sid = f.get("id")
    s = Service.query.get(int(sid)) if sid else Service()
    s.name = f.get("name", "").strip()
    s.description = f.get("description", "").strip() or None
    s.price = int(f.get("price") or 0)
    s.duration_minutes = int(f.get("duration_minutes") or 30)
    s.category = f.get("category", "Barber")
    s.active = f.get("active") == "on"
    db.session.add(s)
    db.session.commit()
    return redirect(url_for("admin.services"))


@admin_bp.route("/services/<int:sid>/toggle", methods=["POST"])
@role_required("super_admin", "manager")
def service_toggle(sid):
    s = Service.query.get_or_404(sid)
    s.active = not s.active
    db.session.commit()
    return redirect(url_for("admin.services"))


# ---------------------------------------------------------------- transactions (4.2d)
@admin_bp.route("/transactions")
@role_required("super_admin", "manager")
def transactions():
    d = request.args.get("date") or date.today().isoformat()
    wid = request.args.get("worker_id", type=int)
    q = Transaction.query.order_by(Transaction.date.desc(), Transaction.id.desc())
    if d:
        q = q.filter_by(date=d)
    if wid:
        q = q.filter_by(worker_id=wid)
    txs = q.limit(200).all()
    workers = Worker.query.filter_by(status="active").order_by(Worker.full_name).all()
    services = Service.query.filter_by(active=True).order_by(Service.category, Service.name).all()
    return render_template("admin/transactions.html", txs=txs, workers=workers,
                           services=services, date=d, worker_id=wid)


@admin_bp.route("/transactions/record", methods=["POST"])
@role_required("super_admin", "manager")
def transaction_record():
    """The most-used screen: quick 'record a service' with automatic commission."""
    f = request.form
    worker = Worker.query.get(int(f.get("worker_id") or 0))
    service_ids = [int(x) for x in f.getlist("service_ids") if x]
    if not worker or not service_ids:
        return "Worker and at least one service are required.", 400

    client = None
    phone = f.get("client_phone", "").strip()
    cid = f.get("client_id")
    if cid:
        client = Client.query.get(int(cid))
    elif phone:
        client = Client.query.filter_by(phone=phone).first()
        if not client:
            client = Client(name=f.get("client_name", "").strip() or "Walk-in", phone=phone)
            db.session.add(client)

    discount = int(f.get("discount") or 0)
    if discount and not (f.get("discount_reason") or "").strip():
        return "A reason is required when applying a discount.", 400

    t = record_transaction(
        worker, service_ids, client=client,
        discount=discount, discount_reason=f.get("discount_reason") or None,
        tip=int(f.get("tip") or 0),
        payment_method=f.get("payment_method", "Cash"),
        note=f.get("note") or None,
        recorded_by=current_user().id,
        date=f.get("date") or date.today().isoformat(),
        time=f.get("time") or date.today().strftime("%H:%M"),
        on_discounted=_setting("commission_on_discounted", "1") == "1",
    )
    db.session.commit()
    return redirect(url_for("admin.transactions", date=t.date))


@admin_bp.route("/transactions/<int:tid>/void", methods=["POST"])
@role_required("super_admin")
def transaction_void(tid):
    """Voiding requires super admin — audit-safe (Section 5.5)."""
    t = Transaction.query.get_or_404(tid)
    t.status = "void"
    if t.client:
        t.client.visit_count = max(0, t.client.visit_count - 1)
        t.client.total_spent = max(0, t.client.total_spent - t.amount)
    db.session.commit()
    return redirect(url_for("admin.transactions", date=t.date))


# ---------------------------------------------------------------- clients (4.2f)
@admin_bp.route("/clients")
@role_required("super_admin", "manager")
def clients():
    q = Client.query.order_by(Client.visit_count.desc()).limit(300).all()
    return render_template("admin/clients.html", clients=q,
                           workers=Worker.query.filter_by(status="active").all())


@admin_bp.route("/clients/save", methods=["POST"])
@role_required("super_admin", "manager")
def client_save():
    f = request.form
    c = Client.query.get(int(f.get("id") or 0)) or Client()
    c.name = f.get("name", "").strip()
    c.phone = f.get("phone", "").strip()
    c.email = f.get("email", "").strip() or None
    c.notes = f.get("notes", "").strip() or None
    pw = f.get("preferred_worker_id")
    c.preferred_worker_id = int(pw) if pw else None
    db.session.add(c)
    db.session.commit()
    return redirect(url_for("admin.clients"))


# ---------------------------------------------------------------- appointments (4.2g)
@admin_bp.route("/appointments")
@role_required("super_admin", "manager")
def appointments():
    d = request.args.get("date") or date.today().isoformat()
    appts = Appointment.query.filter_by(date=d).order_by(Appointment.time).all()
    return render_template("admin/appointments.html", appts=appts, date=d,
                           workers=Worker.query.filter_by(status="active").all(),
                           services=Service.query.filter_by(active=True).all(),
                           clients=Client.query.order_by(Client.name).all())


@admin_bp.route("/appointments/add", methods=["POST"])
@role_required("super_admin", "manager")
def appointment_add():
    """Walk-in booking added directly by staff."""
    f = request.form
    client = Client.query.get(int(f.get("client_id") or 0))
    if not client:
        phone = f.get("client_phone", "").strip()
        client = Client.query.filter_by(phone=phone).first() if phone else None
        if not client:
            client = Client(name=f.get("client_name", "").strip() or "Walk-in",
                            phone=phone or f"walkin-{date.today().isoformat()}")
            db.session.add(client)
    a = Appointment(client_id=client.id, worker_id=int(f.get("worker_id")),
                    service_id=int(f.get("service_id")), date=f.get("date"),
                    time=f.get("time"), status="confirmed", source="walk_in")
    db.session.add(a)
    db.session.commit()
    return redirect(url_for("admin.appointments", date=f.get("date")))


@admin_bp.route("/appointments/<int:aid>/status", methods=["POST"])
@role_required("super_admin", "manager")
def appointment_status(aid):
    """Confirm / complete / cancel / no-show. 'completed' triggers commission."""
    a = Appointment.query.get_or_404(aid)
    new_status = request.form.get("status")
    if new_status not in ("pending", "confirmed", "completed", "cancelled", "no_show"):
        return "Invalid status.", 400
    a.status = new_status
    if new_status == "completed":
        # convert the appointment into a recorded transaction (commission fires)
        record_transaction(Worker.query.get(a.worker_id), [a.service_id],
                          client=Client.query.get(a.client_id),
                          recorded_by=current_user().id, date=a.date, time=a.time,
                          on_discounted=_setting("commission_on_discounted", "1") == "1")
    db.session.commit()
    return redirect(url_for("admin.appointments", date=a.date))


# ---------------------------------------------------------------- inventory (4.2h)
@admin_bp.route("/inventory")
@role_required("super_admin", "manager")
def inventory():
    items = InventoryItem.query.order_by(InventoryItem.category, InventoryItem.item_name).all()
    return render_template("admin/inventory.html", items=items)


@admin_bp.route("/inventory/save", methods=["POST"])
@role_required("super_admin", "manager")
def inventory_save():
    f = request.form
    i = InventoryItem.query.get(int(f.get("id") or 0)) or InventoryItem()
    i.item_name = f.get("item_name", "").strip()
    i.category = f.get("category", "").strip() or None
    i.quantity = float(f.get("quantity") or 0)
    i.unit = f.get("unit", "pcs")
    i.reorder_level = float(f.get("reorder_level") or 0)
    i.unit_cost = int(f.get("unit_cost") or 0)
    db.session.add(i)
    db.session.commit()
    return redirect(url_for("admin.inventory"))


# ---------------------------------------------------------------- expenses (4.2i)
@admin_bp.route("/expenses")
@role_required("super_admin", "manager")
def expenses():
    exps = Expense.query.order_by(Expense.date.desc()).limit(200).all()
    month_start = date.today().isoformat()[:8] + "01"
    month_total = db.session.query(func.coalesce(func.sum(Expense.amount), 0))\
        .filter(Expense.date >= month_start).scalar()
    return render_template("admin/expenses.html", expenses=exps, month_total=month_total,
                           categories=["Rent", "Utilities", "Restocking",
                                       "Equipment", "Salaries", "Other"])


@admin_bp.route("/expenses/save", methods=["POST"])
@role_required("super_admin", "manager")
def expense_save():
    f = request.form
    e = Expense(category=f.get("category", "Other"),
                description=f.get("description", "").strip() or None,
                amount=int(f.get("amount") or 0),
                date=f.get("date") or date.today().isoformat(),
                recorded_by=current_user().id)
    db.session.add(e)
    db.session.commit()
    return redirect(url_for("admin.expenses"))


# ---------------------------------------------------------------- reports (4.2j)
@admin_bp.route("/reports")
@role_required("super_admin", "manager")
def reports():
    month_start = date.today().isoformat()[:8] + "01"
    txs = Transaction.query.filter(Transaction.date >= month_start,
                                   Transaction.status == "completed").all()
    by_service, by_worker, by_category, by_hour = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
    for t in txs:
        by_hour[t.time[:2]] += t.amount
        by_worker[t.worker.full_name] += t.amount
        by_category[t.worker.category] += t.amount
        for it in t.items:
            by_service[it.service_name] += it.price
    top_services = sorted(by_service.items(), key=lambda kv: -kv[1])[:10]
    busiest = sorted(by_hour.items(), key=lambda kv: -kv[1])[:5]
    return render_template("admin/reports.html",
                           top_services=top_services,
                           by_worker=sorted(by_worker.items(), key=lambda kv: -kv[1]),
                           by_category=sorted(by_category.items(), key=lambda kv: -kv[1]),
                           busiest=busiest, month_revenue=sum(t.amount for t in txs),
                           n_tx=len(txs))


# ---------------------------------------------------------------- payroll (4.2e, 5.6)
@admin_bp.route("/payroll")
@role_required("super_admin")
def payroll():
    start = request.args.get("start") or date.today().isoformat()[:8] + "01"
    end = request.args.get("end") or date.today().isoformat()
    rows = []
    for w in Worker.query.order_by(Worker.full_name).all():
        txs = Transaction.query.filter_by(worker_id=w.id, status="completed")\
            .filter(Transaction.date >= start, Transaction.date <= end).all()
        commission = sum(t.commission_amount for t in txs)
        tips = sum(t.tip for t in txs)
        existing = Payroll.query.filter_by(worker_id=w.id,
                                           period_start=start, period_end=end).first()
        bonus = existing.bonus if existing else 0
        deductions = existing.deductions if existing else 0
        if w.pay_type == "fixed":
            net = w.base_salary + bonus - deductions
        elif w.pay_type == "hybrid":
            net = w.base_salary + commission + tips + bonus - deductions
        else:
            net = commission + tips + bonus - deductions
        rows.append({"worker": w, "clients": len(txs),
                     "revenue": sum(t.amount for t in txs),
                     "commission": commission, "tips": tips,
                     "bonus": bonus, "deductions": deductions, "net": net,
                     "existing": existing})
    past = Payroll.query.filter_by(status="paid").order_by(Payroll.id.desc()).limit(50).all()
    return render_template("admin/payroll.html", rows=rows, start=start, end=end, past=past)


@admin_bp.route("/payroll/approve", methods=["POST"])
@role_required("super_admin")
def payroll_approve():
    """Owner reviews and clicks 'Approve & Pay' — generates the payslip record."""
    f = request.form
    start, end = f.get("start"), f.get("end")
    for w in Worker.query.all():
        if f.get(f"skip_{w.id}"):
            continue
        txs = Transaction.query.filter_by(worker_id=w.id, status="completed")\
            .filter(Transaction.date >= start, Transaction.date <= end).all()
        commission = sum(t.commission_amount for t in txs)
        tips = sum(t.tip for t in txs)
        bonus = int(f.get(f"bonus_{w.id}") or 0)
        deductions = int(f.get(f"ded_{w.id}") or 0)
        if w.pay_type == "fixed":
            net = w.base_salary + bonus - deductions
        elif w.pay_type == "hybrid":
            net = w.base_salary + commission + tips + bonus - deductions
        else:
            net = commission + tips + bonus - deductions
        p = Payroll.query.filter_by(worker_id=w.id, period_start=start, period_end=end).first()
        if not p:
            p = Payroll(worker_id=w.id, period_start=start, period_end=end)
        p.total_clients = len(txs)
        p.gross_revenue = sum(t.amount for t in txs)
        p.commission_earned = commission + tips
        p.bonus, p.deductions, p.net_pay = bonus, deductions, net
        p.status = "paid"
        p.paid_date = date.today().isoformat()
        db.session.add(p)
    db.session.commit()
    return redirect(url_for("admin.payroll", start=start, end=end))


# ---------------------------------------------------------------- calendar (4.2n)
@admin_bp.route("/calendar")
@role_required("super_admin", "manager")
def calendar_view():
    """Month heatmap of income / commission / clients; per-worker filter = salary tracker."""
    import calendar as cal
    y = request.args.get("y", type=int) or date.today().year
    m = request.args.get("m", type=int) or date.today().month
    worker_id = request.args.get("worker_id", type=int)
    month_start = f"{y:04d}-{m:02d}-01"
    last = cal.monthrange(y, m)[1]
    month_end = f"{y:04d}-{m:02d}-{last:02d}"

    q = Transaction.query.filter_by(status="completed")\
        .filter(Transaction.date >= month_start, Transaction.date <= month_end)
    if worker_id:
        q = q.filter_by(worker_id=worker_id)
    txs = q.all()

    days = defaultdict(lambda: {"income": 0, "commission": 0, "clients": 0})
    for t in txs:
        d = days[t.date]
        d["income"] += t.amount
        d["commission"] += t.commission_amount + t.tip
        d["clients"] += 1
    max_income = max([d["income"] for d in days.values()], default=1) or 1

    weeks = cal.Calendar(firstweekday=6).monthdayscalendar(y, m)
    return render_template("admin/calendar.html", y=y, m=m, weeks=weeks, days=dict(days),
                           max_income=max_income,
                           workers=Worker.query.filter_by(status="active").all(),
                           worker_id=worker_id,
                           month_income=sum(d["income"] for d in days.values()),
                           month_commission=sum(d["commission"] for d in days.values()),
                           month_clients=sum(d["clients"] for d in days.values()),
                           month_name=cal.month_name[m])


@admin_bp.route("/calendar/day/<day>")
@role_required("super_admin", "manager")
def calendar_day(day):
    """Click into any day to see the full breakdown by worker / service / category."""
    txs = Transaction.query.filter_by(date=day, status="completed")\
        .order_by(Transaction.time).all()
    return render_template("admin/calendar_day.html", day=day, txs=txs,
                          total=sum(t.amount for t in txs),
                          commission=sum(t.commission_amount for t in txs),
                          tips=sum(t.tip for t in txs))


@admin_bp.route("/calendar/export.csv")
@role_required("super_admin", "manager")
def calendar_export():
    """Any selected date range exportable to CSV (opens in Excel)."""
    from flask import Response
    start = request.args.get("start") or date.today().isoformat()[:8] + "01"
    end = request.args.get("end") or date.today().isoformat()
    rows = Transaction.query.filter_by(status="completed")\
        .filter(Transaction.date >= start, Transaction.date <= end)\
        .order_by(Transaction.date).all()
    out = ["date,time,worker,category,services,client,amount,discount,tip,commission,salon,payment"]
    for t in rows:
        names = "; ".join(i.service_name for i in t.items)
        out.append(f"{t.date},{t.time},{t.worker.full_name},{t.worker.category},"
                   f"\"{names}\",{t.client.name if t.client else ''},{t.amount},"
                   f"{t.discount},{t.tip},{t.commission_amount},{t.salon_amount},{t.payment_method}")
    return Response("\n".join(out), mimetype="text/csv",
                    headers={"Content-Disposition":
                             f"attachment;filename=transactions_{start}_{end}.csv"})


# ---------------------------------------------------------------- settings (4.2m)
@admin_bp.route("/settings")
@role_required("super_admin")
def settings():
    keys = ["shop_name", "tagline", "phone", "whatsapp", "address", "hours", "currency",
            "default_commission_rate", "commission_on_discounted",
            "restrict_service_category", "pay_period", "loyalty_visits_for_reward"]
    vals = {k: Setting.get(k, "") for k in keys}
    return render_template("admin/settings.html", settings=vals)


@admin_bp.route("/settings/save", methods=["POST"])
@role_required("super_admin")
def settings_save():
    for k in ("shop_name", "tagline", "phone", "whatsapp", "address", "hours",
              "currency", "default_commission_rate", "commission_on_discounted",
              "restrict_service_category", "pay_period", "loyalty_visits_for_reward"):
        if k in request.form:
            Setting.set(k, request.form[k].strip())
    db.session.commit()
    return redirect(url_for("admin.settings"))


# ---------------------------------------------------------------- worker self-view (4.1)
@admin_bp.route("/my")
@login_required
def my():
    """A logged-in worker sees only their own schedule, clients and earnings."""
    u = current_user()
    w = Worker.query.filter_by(user_id=u.id).first()
    if not w:
        return "Your account is not linked to a worker profile.", 404
    today = date.today().isoformat()
    month_start = today[:8] + "01"
    upcoming = Appointment.query.filter_by(worker_id=w.id)\
        .filter(Appointment.date >= today, Appointment.status.in_(["pending", "confirmed"]))\
        .order_by(Appointment.date, Appointment.time).all()
    month_tx = Transaction.query.filter_by(worker_id=w.id, status="completed")\
        .filter(Transaction.date >= month_start).all()
    return render_template("admin/my.html", w=w, upcoming=upcoming,
                           month_tx=month_tx,
                           month_clients=len(month_tx),
                           month_revenue=sum(t.amount for t in month_tx),
                           month_commission=sum(t.commission_amount for t in month_tx),
                           month_tips=sum(t.tip for t in month_tx),
                           payslips=Payroll.query.filter_by(worker_id=w.id, status="paid")
                                   .order_by(Payroll.id.desc()).limit(12).all())



