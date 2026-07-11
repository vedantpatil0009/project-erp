from models import db

class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    roll_no = db.Column(db.String(20), unique=True)

    department = db.Column(db.String(50))

    semester = db.Column(db.Integer)

    division = db.Column(db.String(10))

    parent_email = db.Column(db.String(120))