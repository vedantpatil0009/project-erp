from models import db


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(100),
        nullable=False
    )

    enrollment_no = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )

    employee_id = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )

    parent_id = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )

    admin_id = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True
    )

    phone = db.Column(
        db.String(20),
        nullable=True
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    def __repr__(self):
        return f"<User {self.full_name}>"
