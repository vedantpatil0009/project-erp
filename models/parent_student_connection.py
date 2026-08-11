from models import db


class ParentStudentConnection(db.Model):
    __tablename__ = "parent_student_connections"
    __table_args__ = (
        db.UniqueConstraint(
            "parent_user_id", "student_user_id", name="uq_parent_student_connection"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    parent_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    student_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
