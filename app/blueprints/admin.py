"""
Admin blueprint — login, dashboard, CRUD for all models, settings.
All mutating routes are protected by Flask-Login + Flask-WTF CSRF.
"""

import os
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from app import db
from app.models.user import User
from app.models.work import Work
from app.models.pricing import PricingPackage, PricingFeature
from app.models.testimonial import Testimonial
from app.models.message import Message
from app.models.settings import SiteSetting
from app.utils import (
    check_rate,
    save_upload,
    save_image_with_thumbnail,
    delete_static_file,
)

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")

# ── Auth ──────────────────────────────────────────────────────────────────────


def _safe_next(target):
    """Only allow same-site relative redirects (blocks open-redirect abuse)."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return None
    return target


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        if not check_rate(f"login:{ip}", max_calls=10, period_seconds=900):
            flash("Too many login attempts. Try again in 15 minutes.", "danger")
            return render_template("admin/login.html"), 429

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = _safe_next(request.args.get("next")) or url_for("admin.dashboard")
            return redirect(next_page)
        flash("Invalid username or password.", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin.login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────


@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "total_works": Work.query.count(),
        "published_works": Work.query.filter_by(published=True).count(),
        "pending_testimonials": Testimonial.query.filter_by(status="pending").count(),
        "unread_messages": Message.query.filter_by(read=False).count(),
        "total_messages": Message.query.count(),
        "approved_testimonials": Testimonial.query.filter_by(status="approved").count(),
    }
    recent_messages = (
        Message.query.order_by(Message.created_at.desc()).limit(5).all()
    )
    recent_testimonials = (
        Testimonial.query.filter_by(status="pending")
        .order_by(Testimonial.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_messages=recent_messages,
        recent_testimonials=recent_testimonials,
    )


# ── Works CRUD ────────────────────────────────────────────────────────────────


@admin_bp.route("/works")
@login_required
def works_list():
    works = Work.query.order_by(Work.category, Work.display_order).all()
    return render_template("admin/works_list.html", works=works)


@admin_bp.route("/works/new", methods=["GET", "POST"])
@login_required
def works_new():
    if request.method == "POST":
        work = _work_from_form(Work())
        if work is None:
            return redirect(url_for("admin.works_new"))
        db.session.add(work)
        db.session.commit()
        flash("Portfolio item created.", "success")
        return redirect(url_for("admin.works_list"))
    return render_template("admin/works_form.html", work=None, action="Create")


@admin_bp.route("/works/<int:pk>/edit", methods=["GET", "POST"])
@login_required
def works_edit(pk: int):
    work = db.get_or_404(Work, pk)
    if request.method == "POST":
        updated = _work_from_form(work)
        if updated is None:
            return redirect(url_for("admin.works_edit", pk=pk))
        db.session.commit()
        flash("Portfolio item updated.", "success")
        return redirect(url_for("admin.works_list"))
    return render_template("admin/works_form.html", work=work, action="Edit")


@admin_bp.route("/works/<int:pk>/delete", methods=["POST"])
@login_required
def works_delete(pk: int):
    work = db.get_or_404(Work, pk)
    delete_static_file(work.file_path or "")
    delete_static_file(work.thumbnail_path or "")
    db.session.delete(work)
    db.session.commit()
    flash("Portfolio item deleted.", "success")
    return redirect(url_for("admin.works_list"))


@admin_bp.route("/works/<int:pk>/toggle-publish", methods=["POST"])
@login_required
def works_toggle_publish(pk: int):
    work = db.get_or_404(Work, pk)
    work.published = not work.published
    db.session.commit()
    state = "published" if work.published else "unpublished"
    flash(f"Work '{work.title}' {state}.", "success")
    return redirect(url_for("admin.works_list"))


def _work_from_form(work: Work):
    """Populate a Work object from form data; returns None on error."""
    work.title = request.form.get("title", "").strip()
    work.description = request.form.get("description", "").strip()
    work.category = request.form.get("category", "").strip()
    work.external_url = request.form.get("external_url", "").strip()
    work.tech_tags = request.form.get("tech_tags", "").strip()
    work.project_url = request.form.get("project_url", "").strip()
    work.featured = bool(request.form.get("featured"))
    work.published = bool(request.form.get("published"))
    try:
        work.display_order = int(request.form.get("display_order", 0))
    except ValueError:
        work.display_order = 0

    if not work.title or not work.category:
        flash("Title and category are required.", "danger")
        return None

    # Handle main file upload
    main_file = request.files.get("file")
    if main_file and main_file.filename:
        cat = work.category
        if cat == "graphic":
            upload_dir = current_app().config["UPLOAD_IMAGES"]
            thumb_dir = current_app().config["UPLOAD_THUMBNAILS"]
            ok, img_path, thumb_path = save_image_with_thumbnail(
                main_file, upload_dir, thumb_dir
            )
            if not ok:
                flash(img_path, "danger")
                return None
            if work.file_path:
                delete_static_file(work.file_path)
            if work.thumbnail_path:
                delete_static_file(work.thumbnail_path)
            work.file_path = img_path
            work.thumbnail_path = thumb_path
        elif cat in ("audio", "music"):
            upload_dir = current_app().config["UPLOAD_AUDIO"]
            ok, path = save_upload(
                main_file, upload_dir, current_app().config["ALLOWED_AUDIO_EXTENSIONS"]
            )
            if not ok:
                flash(path, "danger")
                return None
            if work.file_path:
                delete_static_file(work.file_path)
            work.file_path = path
        elif cat in ("video", "web"):
            upload_dir = current_app().config["UPLOAD_VIDEO"]
            ok, path = save_upload(
                main_file, upload_dir, current_app().config["ALLOWED_VIDEO_EXTENSIONS"]
            )
            if not ok:
                flash(path, "danger")
                return None
            if work.file_path:
                delete_static_file(work.file_path)
            work.file_path = path

    # Handle separate thumbnail upload
    thumb_file = request.files.get("thumbnail")
    if thumb_file and thumb_file.filename:
        thumb_dir = current_app().config["UPLOAD_THUMBNAILS"]
        upload_dir = current_app().config["UPLOAD_IMAGES"]
        ok, img_path, thumb_path = save_image_with_thumbnail(
            thumb_file, upload_dir, thumb_dir
        )
        if not ok:
            flash(img_path, "danger")
            return None
        if work.thumbnail_path:
            delete_static_file(work.thumbnail_path)
        work.thumbnail_path = thumb_path

    return work


def current_app():
    from flask import current_app as _app
    return _app


# ── Pricing CRUD ──────────────────────────────────────────────────────────────


@admin_bp.route("/pricing")
@login_required
def pricing_list():
    packages = (
        PricingPackage.query
        .order_by(PricingPackage.category, PricingPackage.display_order)
        .all()
    )
    return render_template("admin/pricing_list.html", packages=packages)


@admin_bp.route("/pricing/new", methods=["GET", "POST"])
@login_required
def pricing_new():
    if request.method == "POST":
        pkg = _pricing_from_form(PricingPackage())
        db.session.add(pkg)
        db.session.flush()  # get pkg.id

        _save_features(pkg)
        db.session.commit()
        flash("Pricing package created.", "success")
        return redirect(url_for("admin.pricing_list"))
    return render_template("admin/pricing_form.html", pkg=None, action="Create")


@admin_bp.route("/pricing/<int:pk>/edit", methods=["GET", "POST"])
@login_required
def pricing_edit(pk: int):
    pkg = db.get_or_404(PricingPackage, pk)
    if request.method == "POST":
        _pricing_from_form(pkg)
        # Replace features
        for f in pkg.features:
            db.session.delete(f)
        db.session.flush()
        _save_features(pkg)
        db.session.commit()
        flash("Pricing package updated.", "success")
        return redirect(url_for("admin.pricing_list"))
    return render_template("admin/pricing_form.html", pkg=pkg, action="Edit")


@admin_bp.route("/pricing/<int:pk>/delete", methods=["POST"])
@login_required
def pricing_delete(pk: int):
    pkg = db.get_or_404(PricingPackage, pk)
    db.session.delete(pkg)
    db.session.commit()
    flash("Package deleted.", "success")
    return redirect(url_for("admin.pricing_list"))


def _pricing_from_form(pkg: PricingPackage) -> PricingPackage:
    pkg.category = request.form.get("category", "").strip()
    pkg.tier_name = request.form.get("tier_name", "").strip()
    try:
        pkg.price_kes = int(request.form.get("price_kes", 0))
    except ValueError:
        pkg.price_kes = 0
    pkg.price_label = request.form.get("price_label", "").strip()
    pkg.is_popular = bool(request.form.get("is_popular"))
    pkg.active = bool(request.form.get("active"))
    try:
        pkg.display_order = int(request.form.get("display_order", 0))
    except ValueError:
        pkg.display_order = 0
    return pkg


def _save_features(pkg: PricingPackage) -> None:
    texts = request.form.getlist("feature_text")
    included_flags = request.form.getlist("feature_included")
    # included_flags is a list of indices (as strings) that are checked
    included_set = set(included_flags)

    for i, text in enumerate(texts):
        text = text.strip()
        if not text:
            continue
        feat = PricingFeature(
            package_id=pkg.id,
            text=text,
            included=(str(i) in included_set),
            display_order=i,
        )
        db.session.add(feat)


# ── Testimonials ──────────────────────────────────────────────────────────────


@admin_bp.route("/testimonials")
@login_required
def testimonials_list():
    status_filter = request.args.get("status", "pending")
    items = (
        Testimonial.query.filter_by(status=status_filter)
        .order_by(Testimonial.created_at.desc())
        .all()
    )
    counts = {
        "pending": Testimonial.query.filter_by(status="pending").count(),
        "approved": Testimonial.query.filter_by(status="approved").count(),
        "rejected": Testimonial.query.filter_by(status="rejected").count(),
    }
    return render_template(
        "admin/testimonials_list.html",
        items=items,
        counts=counts,
        current_status=status_filter,
    )


@admin_bp.route("/testimonials/<int:pk>/approve", methods=["POST"])
@login_required
def testimonial_approve(pk: int):
    t = db.get_or_404(Testimonial, pk)
    t.status = "approved"
    db.session.commit()
    flash(f"Testimonial from {t.name} approved.", "success")
    return redirect(url_for("admin.testimonials_list", status="pending"))


@admin_bp.route("/testimonials/<int:pk>/reject", methods=["POST"])
@login_required
def testimonial_reject(pk: int):
    t = db.get_or_404(Testimonial, pk)
    t.status = "rejected"
    db.session.commit()
    flash(f"Testimonial from {t.name} rejected.", "warning")
    return redirect(url_for("admin.testimonials_list", status="pending"))


@admin_bp.route("/testimonials/<int:pk>/delete", methods=["POST"])
@login_required
def testimonial_delete(pk: int):
    t = db.get_or_404(Testimonial, pk)
    db.session.delete(t)
    db.session.commit()
    flash("Testimonial deleted.", "success")
    return redirect(url_for("admin.testimonials_list"))


# ── Messages ──────────────────────────────────────────────────────────────────


@admin_bp.route("/messages")
@login_required
def messages_list():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template("admin/messages_list.html", messages=messages)


@admin_bp.route("/messages/<int:pk>")
@login_required
def message_view(pk: int):
    msg = db.get_or_404(Message, pk)
    if not msg.read:
        msg.read = True
        db.session.commit()
    return render_template("admin/message_view.html", msg=msg)


@admin_bp.route("/messages/<int:pk>/delete", methods=["POST"])
@login_required
def message_delete(pk: int):
    msg = db.get_or_404(Message, pk)
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted.", "success")
    return redirect(url_for("admin.messages_list"))


@admin_bp.route("/messages/<int:pk>/toggle-read", methods=["POST"])
@login_required
def message_toggle_read(pk: int):
    msg = db.get_or_404(Message, pk)
    msg.read = not msg.read
    db.session.commit()
    return redirect(url_for("admin.messages_list"))


# ── Settings ──────────────────────────────────────────────────────────────────

SETTING_KEYS = [
    "brand_name",
    "hero_tagline",
    "hero_subtext",
    "hero_cta_primary",
    "hero_cta_secondary",
    "about_bio",
    "about_skills",
    "whatsapp_number",
    "contact_email",
    "instagram_url",
    "twitter_url",
    "linkedin_url",
    "behance_url",
    "soundcloud_url",
    "youtube_url",
]


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    from flask import current_app as app

    if request.method == "POST":
        for key in SETTING_KEYS:
            value = request.form.get(key, "").strip()
            SiteSetting.set(key, value)

        # Logo upload
        logo_file = request.files.get("logo")
        if logo_file and logo_file.filename:
            upload_dir = os.path.join(app.static_folder, "img")
            ok, path = save_upload(
                logo_file, upload_dir, app.config["ALLOWED_IMAGE_EXTENSIONS"]
            )
            if ok:
                SiteSetting.set("logo_path", path)
            else:
                flash(f"Logo upload failed: {path}", "danger")

        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))

    current_settings = SiteSetting.all_as_dict()
    return render_template(
        "admin/settings.html",
        settings=current_settings,
        setting_keys=SETTING_KEYS,
    )
