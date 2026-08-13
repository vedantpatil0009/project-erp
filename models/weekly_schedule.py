from models import db


class WeeklySchedule(db.Model):
    __tablename__ = "weekly_schedules"

    id = db.Column(db.Integer, primary_key=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    day_of_week = db.Column(db.Integer, nullable=False, index=True)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    room = db.Column(db.String(100), nullable=True)
    teacher = db.Column(db.String(100), nullable=True)
    class_type = db.Column(db.String(50), nullable=True)

    student = db.relationship("User")
