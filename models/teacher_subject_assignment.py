from models import db


class TeacherSubjectAssignment(db.Model):
    __tablename__ = "teacher_subject_assignments"

    id = db.Column(db.Integer, primary_key=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    semester = db.Column(db.Integer, nullable=True)
    division = db.Column(db.String(10), nullable=True)

    teacher = db.relationship("User", foreign_keys=[teacher_user_id])
    subject = db.relationship("Subject", foreign_keys=[subject_id])
