"""
Hurtl355 Portfolio — Flask Application Factory
"""

import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

# ── Extension singletons ──────────────────────────────────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

DEFAULT_SECRET = "change-me-in-production"


def _database_url() -> str:
    """Read DATABASE_URL and normalise it for SQLAlchemy + psycopg2.

    Neon / Render hand out `postgres://` or `postgresql://` URLs; SQLAlchemy
    wants `postgresql+psycopg2://`.
    """
    url = os.getenv("DATABASE_URL", "sqlite:///hurtl355.db")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def create_app(config_override: dict | None = None) -> Flask:
    """Create and configure the Flask application."""

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    is_prod = os.getenv("FLASK_ENV", "development").lower() == "production"

    # ── Configuration ─────────────────────────────────────────────────────────
    secret = os.getenv("SECRET_KEY", DEFAULT_SECRET)
    if is_prod and (secret == DEFAULT_SECRET or secret.startswith("change-me")):
        raise RuntimeError(
            "SECRET_KEY must be set to a long random value when FLASK_ENV=production."
        )
    app.config["SECRET_KEY"] = secret

    db_url = _database_url()
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if not db_url.startswith("sqlite"):
        # Neon (and most hosted Postgres) closes idle connections; reconnect quietly.
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 280,
        }

    # Session / cookie hardening
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = is_prod

    # Upload limits & allowed types
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB (Render free tier has 512 MB RAM)
    app.config["ALLOWED_IMAGE_EXTENSIONS"] = {"jpg", "jpeg", "png", "webp"}
    app.config["ALLOWED_AUDIO_EXTENSIONS"] = {"mp3", "wav"}
    app.config["ALLOWED_VIDEO_EXTENSIONS"] = {"mp4"}

    # Upload paths (local fallback when Cloudflare R2 is not configured)
    app.config["UPLOAD_IMAGES"] = os.path.join(app.static_folder, "uploads", "images")
    app.config["UPLOAD_AUDIO"] = os.path.join(app.static_folder, "uploads", "audio")
    app.config["UPLOAD_VIDEO"] = os.path.join(app.static_folder, "uploads", "video")
    app.config["UPLOAD_THUMBNAILS"] = os.path.join(
        app.static_folder, "uploads", "thumbnails"
    )

    # Rate-limiting config (simple in-memory for testimonial form)
    app.config["RATE_LIMIT_TESTIMONIAL"] = int(
        os.getenv("RATE_LIMIT_TESTIMONIAL", "3")
    )

    if config_override:
        app.config.update(config_override)

    # Behind Render / Cloudflare the real client IP is in X-Forwarded-For.
    if is_prod:
        from werkzeug.middleware.proxy_fix import ProxyFix

        hops = int(os.getenv("TRUSTED_PROXIES", "1"))
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=1, x_host=1)

    # ── Initialise extensions ─────────────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.session_protection = "strong"  # log out if the session is replayed from another device
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    # ── User loader ───────────────────────────────────────────────────────────
    from app.models.user import User  # noqa: E402

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # ── Register blueprints ───────────────────────────────────────────────────
    from app.blueprints.public import public_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # The public JSON endpoints (contact / testimonials) are anonymous, protected by
    # a honeypot + rate limit, and called by fetch() without a CSRF token. Without
    # this exemption every visitor submission is rejected with HTTP 400.
    # The admin panel stays fully CSRF-protected.
    csrf.exempt(api_bp)

    # ── Jinja helpers ─────────────────────────────────────────────────────────
    from markupsafe import Markup, escape
    from app.utils import media_url

    @app.template_filter('nl2br')
    def nl2br_filter(value: str) -> Markup:
        """Convert newlines to <br> tags."""
        return Markup(escape(value).replace('\n', Markup('<br/>')))

    # media_url("uploads/images/x.png") -> R2 URL if configured, else /static/...
    app.jinja_env.globals["media_url"] = media_url

    import re

    @app.template_filter("safe_url")
    def safe_url(value) -> str:
        """Allow only http(s), mailto, tel, relative and #anchors in links.
        Blocks `javascript:` and similar tricks if a bad value ever reaches the DB."""
        v = str(value or "").strip()
        if v.startswith("//"):
            return ""
        if re.match(r"^(https?://|mailto:|tel:|/|#)", v, re.I):
            return v
        if re.match(r"^[\w-]+(\.[\w-]+)+(/|$)", v):  # "instagram.com/x" -> add https://
            return "https://" + v
        return ""

    @app.template_filter("digits_only")
    def digits_only(value) -> str:
        return re.sub(r"\D", "", str(value or ""))

    # ── Security headers on every response ────────────────────────────────────
    csp = "; ".join([
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: blob: https:",
        "media-src 'self' blob: https:",
        "frame-src https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ])

    @app.after_request
    def set_security_headers(resp):
        h = resp.headers
        h.setdefault("Content-Security-Policy", csp)
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if is_prod:
            h.setdefault("Strict-Transport-Security", "max-age=31536000")
        # never let browsers/proxies cache the admin panel
        if request.path.startswith("/admin"):
            h["Cache-Control"] = "no-store"
        return resp

    # ── Create tables (safe to run repeatedly) ────────────────────────────────
    with app.app_context():
        db.create_all()

    return app
