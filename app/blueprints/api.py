"""
JSON API blueprint — consumed by public page JS for dynamic loads.
Endpoints:
  GET  /api/works?category=
  GET  /api/pricing
  GET  /api/testimonials
  POST /api/testimonials
  POST /api/contact
"""

import bleach
from flask import Blueprint, jsonify, request
from app import db
from app.models.work import Work
from app.models.pricing import PricingPackage
from app.models.testimonial import Testimonial
from app.models.message import Message
from app.utils import rate_limited

api_bp = Blueprint("api", __name__)

ALLOWED_CATEGORIES = {"graphic", "video", "music", "web"}


# ── Works ─────────────────────────────────────────────────────────────────────

@api_bp.get("/works")
def get_works():
    category = request.args.get("category", "").lower()
    q = Work.query.filter_by(published=True)
    if category and category in ALLOWED_CATEGORIES:
        q = q.filter_by(category=category)
    works = q.order_by(Work.display_order).all()
    return jsonify([w.to_dict() for w in works])


# ── Pricing ───────────────────────────────────────────────────────────────────

@api_bp.get("/pricing")
def get_pricing():
    category = request.args.get("category", "").lower()
    q = PricingPackage.query.filter_by(active=True)
    if category and category in ALLOWED_CATEGORIES:
        q = q.filter_by(category=category)
    packages = q.order_by(PricingPackage.category, PricingPackage.display_order).all()
    return jsonify([p.to_dict() for p in packages])


# ── Testimonials ──────────────────────────────────────────────────────────────

@api_bp.get("/testimonials")
def get_testimonials():
    items = (
        Testimonial.query.filter_by(status="approved")
        .order_by(Testimonial.created_at.desc())
        .all()
    )
    return jsonify([t.to_dict() for t in items])


@api_bp.post("/testimonials")
@rate_limited(max_calls=3, period_seconds=3600)
def post_testimonial():
    data = request.get_json(silent=True) or {}

    # Honeypot check — bots fill the hidden field
    if data.get("website"):
        return jsonify({"ok": True})  # silently discard

    name = bleach.clean(str(data.get("name", "")).strip())[:120]
    role = bleach.clean(str(data.get("role", "")).strip())[:120]
    message = bleach.clean(str(data.get("message", "")).strip())[:2000]

    try:
        rating = int(data.get("rating", 0))
    except (ValueError, TypeError):
        rating = 0

    if not name or not message or rating not in range(1, 6):
        return jsonify({"error": "Name, rating (1-5), and message are required."}), 400

    t = Testimonial(
        name=name,
        role=role,
        rating=rating,
        message=message,
        status="pending",
        ip_address=request.remote_addr or "",
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({"ok": True, "message": "Thank you! Your review is pending approval."})


# ── Contact ───────────────────────────────────────────────────────────────────

@api_bp.post("/contact")
@rate_limited(max_calls=5, period_seconds=3600)
def post_contact():
    data = request.get_json(silent=True) or {}

    # Honeypot
    if data.get("website"):
        return jsonify({"ok": True})

    name = bleach.clean(str(data.get("name", "")).strip())[:120]
    email = bleach.clean(str(data.get("email", "")).strip())[:200]
    service = bleach.clean(str(data.get("service", "")).strip())[:80]
    body = bleach.clean(str(data.get("message", "")).strip())[:5000]

    if not name or not email or not body:
        return jsonify({"error": "Name, email, and message are required."}), 400

    if "@" not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400

    msg = Message(
        name=name,
        email=email,
        service=service,
        body=body,
        ip_address=request.remote_addr or "",
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"ok": True, "message": "Message received! I'll be in touch shortly."})
