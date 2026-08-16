from datetime import date

from models import db


class Attendance(db.Model):
    """Individual attendance taken for one student in one lecture."""

    __tablename__ = "attendance"
    __table_args__ = (
        db.CheckConstraint("status IN ('Present', 'Absent')", name="ck_attendance_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False)

    student = db.relationship("User", foreign_keys=[student_user_id])
    teacher = db.relationship("User", foreign_keys=[teacher_user_id])
    subject = db.relationship("Subject", foreign_keys=[subject_id])
