from datetime import datetime

from models import db


class StudentResult(db.Model):
    __tablename__ = "student_results"
    __table_args__ = (db.UniqueConstraint("student_user_id", "subject", "exam", name="uq_student_result_exam"),)

    id = db.Column(db.Integer, primary_key=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject = db.Column(db.String(100), nullable=False)
    exam = db.Column(db.String(150), nullable=False)
    marks_grade = db.Column(db.String(50), nullable=False)
    out_of_marks = db.Column(db.Float, nullable=False, default=100)
    is_internal = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = db.relationship("User", foreign_keys=[student_user_id])
    teacher = db.relationship("User", foreign_keys=[teacher_user_id])
