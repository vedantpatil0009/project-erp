from datetime import datetime

from models import db


class StudentNotification(db.Model):
    __tablename__ = "student_notifications"
    __table_args__ = (
        db.UniqueConstraint("student_user_id", "material_id", name="uq_student_material_notification"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey("academic_materials.id"), nullable=False, index=True)
    material_type = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    teacher_name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship("User", foreign_keys=[student_user_id])
    material = db.relationship("AcademicMaterial", foreign_keys=[material_id])
