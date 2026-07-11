from models import db

class Teacher(db.Model):

    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey("users.id"),
                        nullable=False)

    employee_id = db.Column(db.String(20), unique=True)

    department = db.Column(db.String(50))

    designation = db.Column(db.String(50))