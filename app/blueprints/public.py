"""
Public-facing blueprint — serves the single-page portfolio.
"""

from flask import Blueprint, render_template
from app.models.settings import SiteSetting
from app.models.work import Work
from app.models.pricing import PricingPackage
from app.models.testimonial import Testimonial

public_bp = Blueprint("public", __name__)

# Default settings used when DB has no values yet
DEFAULTS = {
    "brand_name": "Hurtl355",
    "hero_tagline": "Code. Design. Sound. Vision.",
    "hero_subtext": "IT Support & Web Dev · Graphic Design · Video Editing · Music Production",
    "hero_cta_primary": "View Work",
    "hero_cta_secondary": "Hire Us",
    "about_bio": (
        "I'm a Nairobi-based software engineer and multidisciplinary creative operating "
        "under the Hurtl355 brand. I blend technical precision with artistic sensibility "
        "to deliver digital products that look stunning and work flawlessly. Whether you "
        "need a blazing-fast website, a jaw-dropping brand identity, a cinematic edit, or "
        "a radio-ready mix — I've got you."
    ),
    "about_skills": "Python,JavaScript,React,Flask,Figma,Adobe Suite,Premiere Pro,Logic Pro X,FL Studio,Node.js",
    "whatsapp_number": "+254700000000",
    "contact_email": "hello@hurtl355.com",
    "instagram_url": "#",
    "twitter_url": "#",
    "linkedin_url": "#",
    "behance_url": "#",
    "soundcloud_url": "#",
    "youtube_url": "#",
    "logo_path": "",
}


def get_settings() -> dict:
    """Return merged settings (DB overrides defaults)."""
    saved = SiteSetting.all_as_dict()
    merged = dict(DEFAULTS)
    merged.update(saved)
    return merged


@public_bp.route("/")
def index():
    settings = get_settings()

    # Featured works for hero area (max 6)
    featured_works = (
        Work.query.filter_by(published=True, featured=True)
        .order_by(Work.display_order)
        .limit(6)
        .all()
    )

    # All published works grouped by category
    all_works = (
        Work.query.filter_by(published=True)
        .order_by(Work.display_order)
        .all()
    )

    # Pricing packages active, grouped
    pricing = (
        PricingPackage.query.filter_by(active=True)
        .order_by(PricingPackage.category, PricingPackage.display_order)
        .all()
    )

    pricing_categories = {}
    for pkg in pricing:
        pricing_categories.setdefault(pkg.category, []).append(pkg)

    # Approved testimonials
    testimonials = (
        Testimonial.query.filter_by(status="approved")
        .order_by(Testimonial.created_at.desc())
        .all()
    )

    # Skills list
    skills = [s.strip() for s in settings.get("about_skills", "").split(",") if s.strip()]

    return render_template(
        "public/index.html",
        settings=settings,
        featured_works=featured_works,
        all_works=all_works,
        pricing_categories=pricing_categories,
        pricing_category_order=["web", "graphic", "video", "music"],
        pricing_category_labels={
            "web": "IT & Web Dev",
            "graphic": "Graphic Design",
            "video": "Video Editing",
            "music": "Music Production",
        },
        testimonials=testimonials,
        skills=skills,
    )


@public_bp.route("/healthz")
def healthz():
    """Lightweight uptime check (no database call)."""
    return "ok", 200
