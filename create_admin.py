"""One-time interactive setup for the first Educon Admin account."""

from getpass import getpass

from sqlalchemy import func

from app import app, bcrypt
from models import db
from models.user import User


def create_admin():
    name = input("Admin Name: ").strip()
    email = input("Admin Email: ").strip()
    admin_id = input("Admin ID: ").strip()
    password = getpass("Password: ")

    if not all((name, email, admin_id, password)):
        print("Admin name, email, ID, and password are all required.")
        return

    with app.app_context():
        if User.query.filter_by(admin_id=admin_id).first():
            print("An account with that Admin ID already exists.")
            return

        if User.query.filter(func.lower(User.email) == email.casefold()).first():
            print("An account with that email already exists.")
            return

        admin = User(
            full_name=name,
            email=email,
            admin_id=admin_id,
            password=bcrypt.generate_password_hash(password).decode("utf-8"),
            role="Admin",
        )
        db.session.add(admin)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            print("Unable to create the Admin account.")
            return

    print(f"Admin account '{admin_id}' created successfully.")


if __name__ == "__main__":
    create_admin()
