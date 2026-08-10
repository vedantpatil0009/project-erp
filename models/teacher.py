from models import db


class Teacher(db.Model):

    __tablename__ = "teachers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    department = db.Column(
        db.String(50),
        nullable=True
    )

    subject = db.Column(
        db.String(100),
        nullable=True
    )