from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from flask_bcrypt import Bcrypt
from sqlalchemy import inspect, text

from config import Config
from models import db

from models.user import User
from models.student import Student
from models.teacher import Teacher


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

bcrypt = Bcrypt(app)


ROLE_IDENTIFIER_FIELDS = {
    "Student": "enrollment_no",
    "Teacher": "employee_id",
    "Parent": "parent_id",
    "Admin": "admin_id",
}

ROLE_DASHBOARD_ENDPOINTS = {
    "Student": "student",
    "Teacher": "teacher",
    "Parent": "parent",
    "Admin": "admin",
}

PUBLIC_REGISTRATION_ROLES = {"Student", "Teacher", "Parent"}

STUDENT_SECTION_CONFIG = {
    "attendance": ("Attendance", "fa-user-check", "No attendance records available."),
    "materials": ("Study Materials", "fa-book", "No study materials available yet."),
    "timetable": ("Timetable", "fa-calendar-days", "No timetable is available yet."),
    "calendar": ("Academic Calendar", "fa-calendar-week", "No academic calendar events are available."),
    "assignments": ("Assignments", "fa-file-lines", "No assignments available yet."),
    "results": ("Results", "fa-square-poll-vertical", "No result records available."),
    "fees": ("Fees", "fa-wallet", "No fee information available."),
    "library": ("Library", "fa-book-open-reader", "No library records available."),
    "notices": ("Notices", "fa-bell", "No notices available yet."),
    "settings": ("Settings", "fa-gear", "No student settings are available yet."),
}


def ensure_user_identifier_columns():
    """Bring the pre-existing SQLite users table in line with User's ID fields."""
    inspector = inspect(db.engine)
    user_columns = {
        column["name"] for column in inspector.get_columns("users")
    }

    with db.engine.begin() as connection:
        for column_name in ROLE_IDENTIFIER_FIELDS.values():
            if column_name not in user_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE users "
                        f"ADD COLUMN {column_name} VARCHAR(50)"
                    )
                )

            connection.execute(
                text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS "
                    f"ux_users_{column_name} "
                    f"ON users ({column_name}) "
                    f"WHERE {column_name} IS NOT NULL"
                )
            )

        if "phone" not in user_columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
            )


def ensure_student_profile_columns():
    """Add the profile fields required by the existing Student model."""
    inspector = inspect(db.engine)
    student_columns = {
        column["name"] for column in inspector.get_columns("students")
    }

    if "phone" not in student_columns:
        with db.engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE students ADD COLUMN phone VARCHAR(20)")
            )


def ensure_teacher_profile_columns():
    """Keep the existing teachers table compatible with the Teacher model."""
    inspector = inspect(db.engine)
    teacher_columns = {
        column["name"] for column in inspector.get_columns("teachers")
    }

    if "subject" not in teacher_columns:
        with db.engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE teachers ADD COLUMN subject VARCHAR(100)")
            )


def get_current_student_profile():
    """Return the logged-in Student user and their Student profile record."""
    if session.get("role") != "Student" or "user_id" not in session:
        return None, None

    user = db.session.get(User, session["user_id"])
    if not user or user.role != "Student":
        session.clear()
        return None, None

    student_profile = Student.query.filter_by(user_id=user.id).first()
    if not student_profile:
        student_profile = Student(user_id=user.id)
        db.session.add(student_profile)
        db.session.commit()

    return user, student_profile


def get_current_user_for_role(role):
    if session.get("role") != role or "user_id" not in session:
        return None

    user = db.session.get(User, session["user_id"])
    if not user or user.role != role:
        session.clear()
        return None

    return user


def render_student_section(section_name):
    user, student_profile = get_current_student_profile()
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    title, icon, empty_message = STUDENT_SECTION_CONFIG[section_name]
    return render_template(
        "student_section.html",
        current_user=user,
        student_profile=student_profile,
        active_page=section_name,
        section_title=title,
        section_icon=icon,
        empty_message=empty_message
    )


# ==========================================
# LANDING PAGE
# ==========================================

@app.route("/")
def landing():
    return render_template("landing.html")


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        session.clear()
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        identifier_field = ROLE_IDENTIFIER_FIELDS.get(role)

        user = None
        if identifier_field and login_id and password:
            user = User.query.filter_by(
                **{identifier_field: login_id, "role": role}
            ).first()

        password_matches = False
        if user:
            try:
                password_matches = bcrypt.check_password_hash(
                    user.password,
                    password
                )
            except ValueError:
                password_matches = False

        if password_matches:
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            return redirect(url_for(ROLE_DASHBOARD_ENDPOINTS[user.role]))

        flash("Invalid ID or Password!")

        return redirect(
            url_for("login")
        )

    return render_template("login.html")


# ==========================================
# REGISTER
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone", "").strip() or None
        department = request.form.get("department", "").strip() or None
        password = request.form.get("password")
        role = request.form.get("role")

        enrollment_no = request.form.get(
            "enrollment_no"
        )

        employee_id = request.form.get(
            "employee_id"
        )

        parent_id = request.form.get(
            "parent_id"
        )

        if role not in PUBLIC_REGISTRATION_ROLES:
            flash("Please select a valid registration role.")
            return redirect(url_for("register"))

        print("Name:", full_name)
        print("Email:", email)
        print("Role:", role)

        # -------------------------
        # CHECK EMAIL
        # -------------------------

        if email:

            existing_email = User.query.filter_by(
                email=email
            ).first()

            if existing_email:

                flash(
                    "Email already registered!"
                )

                return redirect(
                    url_for("register")
                )

        # -------------------------
        # CHECK STUDENT ID
        # -------------------------

        if role == "Student":

            if not enrollment_no:

                flash(
                    "Enrollment Number is required!"
                )

                return redirect(
                    url_for("register")
                )

            existing_id = User.query.filter_by(
                enrollment_no=enrollment_no
            ).first()

            if existing_id:

                flash(
                    "Enrollment Number already registered!"
                )

                return redirect(
                    url_for("register")
                )

        # -------------------------
        # CHECK TEACHER ID
        # -------------------------

        elif role == "Teacher":

            if not employee_id:

                flash(
                    "Employee ID is required!"
                )

                return redirect(
                    url_for("register")
                )

            existing_id = User.query.filter_by(
                employee_id=employee_id
            ).first()

            if existing_id:

                flash(
                    "Employee ID already registered!"
                )

                return redirect(
                    url_for("register")
                )

        # -------------------------
        # CHECK PARENT ID
        # -------------------------

        elif role == "Parent":

            if not parent_id:

                flash(
                    "Parent ID is required!"
                )

                return redirect(
                    url_for("register")
                )

            existing_id = User.query.filter_by(
                parent_id=parent_id
            ).first()

            if existing_id:

                flash(
                    "Parent ID already registered!"
                )

                return redirect(
                    url_for("register")
                )

        # -------------------------
        # HASH PASSWORD
        # -------------------------

        hashed_password = (
            bcrypt
            .generate_password_hash(password)
            .decode("utf-8")
        )

        # -------------------------
        # CREATE USER
        # -------------------------

        new_user = User(

            full_name=full_name,

            email=email,

            phone=phone,

            password=hashed_password,

            role=role,

            enrollment_no=(
                enrollment_no
                if role == "Student"
                else None
            ),

            employee_id=(
                employee_id
                if role == "Teacher"
                else None
            ),

            parent_id=(
                parent_id
                if role == "Parent"
                else None
            )
        )

        db.session.add(new_user)
        db.session.flush()

        if role == "Student":
            db.session.add(Student(
                user_id=new_user.id,
                phone=phone,
                department=department
            ))
        elif role == "Teacher":
            db.session.add(Teacher(
                user_id=new_user.id,
                department=department
            ))

        db.session.commit()

        print(
            "USER SAVED:",
            new_user.id,
            new_user.full_name
        )

        flash(
            "Registration Successful!"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ==========================================
# STUDENT DASHBOARD
# ==========================================

@app.route("/student")
def student():

    user, student_profile = get_current_student_profile()
    if not user:
        flash("Access denied!")
        return redirect(
            url_for("login")
        )

    return render_template(
        "student.html",
        current_user=user,
        student_profile=student_profile,
        active_page="dashboard"
    )


@app.route("/student/profile")
def student_profile():
    user, profile = get_current_student_profile()
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    return render_template(
        "student_profile.html",
        current_user=user,
        student_profile=profile,
        active_page="profile"
    )


@app.route("/student/profile/edit", methods=["GET", "POST"])
def edit_student_profile():
    user, profile = get_current_student_profile()
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        semester_value = request.form.get("semester", "").strip()

        if not full_name or not email:
            flash("Full name and email are required.")
            return redirect(url_for("edit_student_profile"))

        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()
        if existing_email:
            flash("Email already registered!")
            return redirect(url_for("edit_student_profile"))

        try:
            semester = int(semester_value) if semester_value else None
        except ValueError:
            flash("Semester must be a number.")
            return redirect(url_for("edit_student_profile"))

        user.full_name = full_name
        user.email = email
        user.phone = request.form.get("phone", "").strip() or None
        profile.phone = user.phone
        profile.department = request.form.get("department", "").strip() or None
        profile.semester = semester
        profile.division = request.form.get("division", "").strip() or None
        profile.parent_email = request.form.get("parent_email", "").strip() or None
        db.session.commit()

        flash("Profile updated successfully!")
        return redirect(url_for("student_profile"))

    return render_template(
        "edit_student_profile.html",
        current_user=user,
        student_profile=profile,
        active_page="profile"
    )


@app.route("/student/attendance")
def student_attendance():
    return render_student_section("attendance")


@app.route("/student/materials")
def student_materials():
    return render_student_section("materials")


@app.route("/student/timetable")
def student_timetable():
    return render_student_section("timetable")


@app.route("/student/calendar")
def student_calendar():
    return render_student_section("calendar")


@app.route("/student/assignments")
def student_assignments():
    return render_student_section("assignments")


@app.route("/student/results")
def student_results():
    return render_student_section("results")


@app.route("/student/fees")
def student_fees():
    return render_student_section("fees")


@app.route("/student/library")
def student_library():
    return render_student_section("library")


@app.route("/student/notices")
def student_notices():
    return render_student_section("notices")


@app.route("/student/settings")
def student_settings():
    return render_student_section("settings")


# ==========================================
# TEACHER DASHBOARD
# ==========================================

@app.route("/teacher")
def teacher():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(
            url_for("login")
        )

    teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
    return render_template(
        "teacher.html",
        current_user=user,
        teacher_profile=teacher_profile
    )


# ==========================================
# PARENT DASHBOARD
# ==========================================

@app.route("/parent")
def parent():
    user = get_current_user_for_role("Parent")
    if not user:
        flash("Access denied!")
        return redirect(
            url_for("login")
        )

    connected_students = []
    if user.email:
        for profile in Student.query.filter_by(parent_email=user.email).all():
            student_user = db.session.get(User, profile.user_id)
            if student_user and student_user.role == "Student":
                connected_students.append((student_user, profile))

    return render_template(
        "parent.html",
        current_user=user,
        connected_students=connected_students
    )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin")
def admin():
    user = get_current_user_for_role("Admin")
    if not user:
        flash("Access denied!")
        return redirect(
            url_for("login")
        )

    students = User.query.filter_by(role="Student").all()
    teachers = User.query.filter_by(role="Teacher").all()
    parents = User.query.filter_by(role="Parent").all()
    return render_template(
        "admin.html",
        current_user=user,
        students=students,
        teachers=teachers,
        parents=parents
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out."
    )

    return redirect(
        url_for("login")
    )


# ==========================================
# CREATE DATABASE
# ==========================================

with app.app_context():

    db.create_all()
    ensure_user_identifier_columns()
    ensure_student_profile_columns()
    ensure_teacher_profile_columns()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
