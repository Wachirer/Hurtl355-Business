"""Portfolio work / project model."""

from datetime import datetime
from app import db


class Work(db.Model):
    __tablename__ = "works"

    id = db.Column(db.Integer, primary_key=True)

    # Core fields
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    category = db.Column(
        db.String(50), nullable=False
    )  # graphic | video | music | web

    # Media — either an uploaded file path (relative to static/) or external URL
    file_path = db.Column(db.String(500))        # uploaded file
    external_url = db.Column(db.String(500))     # YouTube, Vimeo, Spotify, SoundCloud, live site …
    thumbnail_path = db.Column(db.String(500))   # always a local image path

    # Web/IT specific
    tech_tags = db.Column(db.String(300), default="")   # comma-separated
    project_url = db.Column(db.String(500))             # live link

    # Display
    featured = db.Column(db.Boolean, default=False)
    published = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Helpers ───────────────────────────────────────────────────────────────
    @property
    def tags_list(self) -> list[str]:
        """Return tech_tags as a list."""
        return [t.strip() for t in self.tech_tags.split(",") if t.strip()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "file_path": self.file_path,
            "external_url": self.external_url,
            "thumbnail_path": self.thumbnail_path,
            "tech_tags": self.tags_list,
            "project_url": self.project_url,
            "featured": self.featured,
            "display_order": self.display_order,
        }

    def __repr__(self) -> str:
        return f"<Work {self.title} [{self.category}]>"
