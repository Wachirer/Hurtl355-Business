"""Pricing package and feature models."""

from app import db


class PricingPackage(db.Model):
    __tablename__ = "pricing_packages"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # graphic | video | music | web
    tier_name = db.Column(db.String(80), nullable=False)  # Basic | Standard | Premium
    price_kes = db.Column(db.Integer, nullable=False, default=0)
    price_label = db.Column(db.String(30), default="")    # e.g. "/ project" or "/ month"
    is_popular = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    features = db.relationship(
        "PricingFeature", backref="package", lazy=True, cascade="all, delete-orphan",
        order_by="PricingFeature.display_order"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "tier_name": self.tier_name,
            "price_kes": self.price_kes,
            "price_label": self.price_label,
            "is_popular": self.is_popular,
            "display_order": self.display_order,
            "features": [f.to_dict() for f in self.features],
        }

    def __repr__(self) -> str:
        return f"<PricingPackage {self.category}/{self.tier_name}>"


class PricingFeature(db.Model):
    __tablename__ = "pricing_features"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer, db.ForeignKey("pricing_packages.id"), nullable=False
    )
    text = db.Column(db.String(300), nullable=False)
    included = db.Column(db.Boolean, default=True)  # True = ✓, False = ✗
    display_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {"id": self.id, "text": self.text, "included": self.included}

    def __repr__(self) -> str:
        return f"<PricingFeature {self.text[:30]}>"
