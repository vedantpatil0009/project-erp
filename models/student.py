from models import db


class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    roll_no = db.Column(
        db.String(20),
        unique=True,
        nullable=True
    )

    department = db.Column(
        db.String(50),
        nullable=True
    )

    semester = db.Column(
        db.Integer,
        nullable=True
    )

    division = db.Column(
        db.String(10),
        nullable=True
    )

    parent_email = db.Column(
        db.String(120),
        nullable=True
    )

    phone = db.Column(
        db.String(20),
        nullable=True
    )
