# Models package — import everything so SQLAlchemy discovers all tables
from app.models.user import User
from app.models.work import Work
from app.models.pricing import PricingPackage, PricingFeature
from app.models.testimonial import Testimonial
from app.models.message import Message
from app.models.settings import SiteSetting

__all__ = [
    "User",
    "Work",
    "PricingPackage",
    "PricingFeature",
    "Testimonial",
    "Message",
    "SiteSetting",
]
