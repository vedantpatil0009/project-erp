from datetime import datetime

from models import db


class AcademicMaterial(db.Model):
    __tablename__ = "academic_materials"

    id = db.Column(db.Integer, primary_key=True)
    teacher_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    material_type = db.Column(db.String(30), nullable=False, index=True)
    department = db.Column(db.String(50), nullable=False, index=True)
    subject = db.Column(db.String(100), nullable=True, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    stored_filename = db.Column(db.String(255), nullable=True, unique=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    teacher = db.relationship("User", foreign_keys=[teacher_user_id])
