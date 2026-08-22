from models import db
from flask_login import UserMixin


class User(UserMixin, db.Model):

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

    theme = db.Column(db.String(20), nullable=False, default="light", server_default="light")
    notifications_enabled = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    accent_color = db.Column(db.String(20), nullable=False, default="purple", server_default="purple")

    def __repr__(self):
        return f"<User {self.full_name}>"
