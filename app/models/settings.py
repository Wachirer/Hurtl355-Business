"""Key-value site settings model."""

from app import db


class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.Text, default="")

    # ── Class helpers ─────────────────────────────────────────────────────────
    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        row = cls.query.filter_by(key=key).first()
        return row.value if row else default

    @classmethod
    def set(cls, key: str, value: str) -> None:
        row = cls.query.filter_by(key=key).first()
        if row:
            row.value = value
        else:
            db.session.add(cls(key=key, value=value))
        db.session.commit()

    @classmethod
    def all_as_dict(cls) -> dict:
        return {row.key: row.value for row in cls.query.all()}

    def __repr__(self) -> str:
        return f"<SiteSetting {self.key}={self.value[:30]}>"
