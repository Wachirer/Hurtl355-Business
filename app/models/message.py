"""Contact form message model."""

from datetime import datetime
from app import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    service = db.Column(db.String(80), default="")
    body = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Message from {self.name} [{self.email}]>"
