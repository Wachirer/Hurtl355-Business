"""Testimonial model — public submissions, admin approval."""

from datetime import datetime
from app import db


class Testimonial(db.Model):
    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), default="")       # optional job title / company
    rating = db.Column(db.Integer, nullable=False)     # 1 – 5
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending | approved | rejected
    ip_address = db.Column(db.String(45), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "rating": self.rating,
            "message": self.message,
            "date": self.created_at.strftime("%B %Y"),
        }

    def __repr__(self) -> str:
        return f"<Testimonial {self.name} ({self.status})>"
