/* SUS KIGALI HAIRCUT — booking flow (Section 3.2)
   Chains: service -> workers (by category) -> date -> live availability -> submit. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var serviceSel = $("service"), workerSel = $("worker"),
      dateInput = $("date"), timeSel = $("time"),
      form = $("booking-form"), msg = $("booking-msg");

  // date can't be in the past
  var today = new Date().toISOString().split("T")[0];
  dateInput.min = today;

  function getJSON(url, cb) {
    fetch(url).then(function (r) { return r.json(); }).then(cb).catch(function () { cb(null); });
  }

  // 1. service chosen -> load matching workers
  serviceSel.addEventListener("change", function () {
    var opt = serviceSel.options[serviceSel.selectedIndex];
    var category = opt ? opt.dataset.category : "";
    workerSel.innerHTML = '<option value="" disabled selected>Loading…</option>';
    timeSel.innerHTML = '<option value="" disabled selected>Select a date first…</option>';
    getJSON("/api/workers?category=" + encodeURIComponent(category), function (workers) {
      workerSel.innerHTML = "";
      if (!workers || !workers.length) {
        workerSel.innerHTML = '<option value="" disabled selected>No one available for this service</option>';
        return;
      }
      if (workers.length > 1) {
        workerSel.add(new Option("Any available", "any"));
      }
      workers.forEach(function (w) {
        var t = w.name + (w.specialty ? " — " + w.specialty : "");
        workerSel.add(new Option(t, w.id));
      });
      workerSel.disabled = false;
    });
  });

  // 2. worker chosen -> (optionally reset time)
  workerSel.addEventListener("change", function () {
    timeSel.innerHTML = '<option value="" disabled selected>Select a date first…</option>';
    if (dateInput.value) { loadTimes(); }
  });

  // 3. date chosen -> load real-time availability
  dateInput.addEventListener("change", function () { if (workerSel.value) { loadTimes(); } });

  function loadTimes() {
    timeSel.innerHTML = '<option value="" disabled selected>Checking availability…</option>';
    var url = "/api/availability?date=" + encodeURIComponent(dateInput.value) +
              "&worker_id=" + encodeURIComponent(workerSel.value || "any");
    getJSON(url, function (slots) {
      timeSel.innerHTML = "";
      if (!slots || !slots.length) {
        timeSel.innerHTML = '<option value="" disabled selected>Fully booked — try another day</option>';
        return;
      }
      timeSel.add(new Option("Select a time…", ""));
      slots.forEach(function (s) { timeSel.add(new Option(s, s)); });
    });
  }

  // 4. submit
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    msg.textContent = "";
    msg.className = "booking-msg";
    fetch("/api/book", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        service_id: serviceSel.value,
        worker_id: workerSel.value,
        date: dateInput.value,
        time: timeSel.value,
        name: $("name").value,
        phone: $("phone").value
      })
    }).then(function (r) { return r.json(); }).then(function (data) {
      msg.textContent = data.ok ? data.message : data.error;
      msg.className = "booking-msg " + (data.ok ? "ok" : "err");
      if (data.ok) {
        form.reset();
        workerSel.innerHTML = '<option value="" disabled selected>Select a service first…</option>';
        timeSel.innerHTML = '<option value="" disabled selected>Select a date first…</option>';
      }
    }).catch(function () {
      msg.textContent = "Could not reach the shop. Please call us instead.";
      msg.className = "booking-msg err";
    });
  });
})();
