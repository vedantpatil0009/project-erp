import os
import uuid
import calendar as calendar_module
from datetime import datetime

from flask import (
    Flask,
    abort,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
)

from flask_bcrypt import Bcrypt
from sqlalchemy import func, inspect, text
from werkzeug.utils import secure_filename

from config import Config
from models import db

from models.user import User
from models.student import Student
from models.teacher import Teacher
from models.academic_material import AcademicMaterial
from models.department import Department
from models.parent_student_connection import ParentStudentConnection
from models.weekly_schedule import WeeklySchedule


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
DEFAULT_DEPARTMENTS = [
    "Computer Engineering",
    "Civil Engineering",
    "Electronics Engineering",
    "Mechanical Engineering",
]

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

MATERIAL_TYPE_BY_SECTION = {
    "attendance": "Attendance",
    "materials": "Study Material",
    "timetable": "Timetable",
    "calendar": "Academic Calendar",
    "assignments": "Assignment",
    "results": "Result",
    "notices": "Notice",
}

MATERIAL_UPLOAD_RULES = {
    "Assignment": {
        "extensions": ["pdf"],
        "file_required": True,
        "description_required": False,
        "file_label": "PDF file",
    },
    "Study Material": {
        "extensions": ["pdf", "doc", "docx", "ppt", "pptx"],
        "file_required": True,
        "description_required": False,
        "file_label": "PDF, DOC, DOCX, PPT, or PPTX file",
    },
    "Timetable": {
        "extensions": ["pdf", "jpg", "jpeg", "png"],
        "file_required": True,
        "description_required": False,
        "file_label": "PDF, JPG, JPEG, or PNG file",
    },
    "Result": {
        "extensions": ["pdf"],
        "file_required": True,
        "description_required": False,
        "file_label": "PDF file",
    },
    "Attendance": {
        "extensions": ["pdf"],
        "file_required": True,
        "description_required": False,
        "file_label": "PDF file",
    },
    "Notice": {
        "extensions": ["pdf"],
        "file_required": False,
        "description_required": True,
        "file_label": "Optional PDF attachment",
    },
    "Academic Calendar": {
        "extensions": ["pdf"],
        "file_required": True,
        "description_required": False,
        "file_label": "PDF file",
    },
}
MATERIAL_TYPES = set(MATERIAL_UPLOAD_RULES)
SUBJECT_MATERIAL_TYPES = {"Assignment", "Study Material"}
SUBJECT_FILTER_SECTIONS = {
    "assignments", "materials", "notices", "results", "attendance",
}
MATERIAL_UPLOAD_FOLDER = os.path.join(
    app.root_path, "static", "uploads", "materials"
)

ROLE_NAV_ITEMS = {
    "Teacher": [
        ("teacher", "Dashboard", "fa-house"),
        ("teacher_profile", "Profile", "fa-circle-user"),
        ("teacher_students", "Students", "fa-users"),
        ("teacher_attendance", "Attendance", "fa-user-check"),
        ("teacher_materials", "Study Material", "fa-book"),
        ("teacher_assignments", "Assignments", "fa-file-lines"),
        ("manage_materials", "Manage Materials", "fa-folder-plus"),
    ],
    "Parent": [
        ("parent", "Dashboard", "fa-house"),
        ("parent_students", "My Students", "fa-user-graduate"),
        ("parent_results", "Results", "fa-square-poll-vertical"),
        ("parent_attendance", "Attendance", "fa-user-check"),
        ("parent_calendar", "Academic Calendar", "fa-calendar-week"),
        ("parent_notices", "Notices", "fa-bell"),
    ],
    "Admin": [
        ("admin", "Dashboard", "fa-house"),
        ("manage_departments", "Departments", "fa-building"),
        ("admin_students", "Students", "fa-user-graduate"),
        ("admin_teachers", "Teachers", "fa-chalkboard-user"),
        ("admin_parents", "Parents", "fa-people-group"),
    ],
}

ROLE_SECTION_CONFIG = {
    "Teacher": {
        "students": ("Students", "fa-users", ["Name", "Enrollment Number", "Department", "Semester"], "No students are assigned to your department."),
        "attendance": ("Attendance", "fa-user-check", ["Student", "Subject", "Date", "Status"], "No attendance records are available yet."),
        "materials": ("Study Material", "fa-book", ["Title", "Subject", "Uploaded On"], "You have not uploaded any study material yet."),
        "assignments": ("Assignments", "fa-file-lines", ["Assignment", "Subject", "Due Date", "Status"], "You have not created any assignments yet."),
    },
    "Parent": {
        "students": ("My Students", "fa-user-graduate", ["Name", "Enrollment Number", "Department", "Semester", "Division"], "No student is connected to this parent account."),
        "notices": ("Notices", "fa-bell", ["Notice", "Published On", "Posted By"], "No notices are available yet."),
    },
    "Admin": {
        "students": ("Students", "fa-user-graduate", ["Name", "Enrollment Number", "Email", "Phone"], "No students are registered yet."),
        "teachers": ("Teachers", "fa-chalkboard-user", ["Name", "Employee ID", "Email", "Phone"], "No teachers are registered yet."),
        "parents": ("Parents", "fa-people-group", ["Name", "Parent ID", "Email", "Phone"], "No parents are registered yet."),
    },
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
        if "theme" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN theme VARCHAR(20) DEFAULT 'light'"))
        if "notifications_enabled" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN notifications_enabled BOOLEAN DEFAULT 1"))
        if "accent_color" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN accent_color VARCHAR(20) DEFAULT 'purple'"))


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


def ensure_academic_material_columns():
    """Add the subject field without recreating the existing materials table."""
    inspector = inspect(db.engine)
    material_columns = {
        column["name"] for column in inspector.get_columns("academic_materials")
    }

    if "subject" not in material_columns:
        with db.engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE academic_materials ADD COLUMN subject VARCHAR(100)")
            )


def seed_departments():
    """Create defaults and preserve department names already used by the app."""
    existing_names = {department.name.casefold() for department in Department.query.all()}
    department_names = set(DEFAULT_DEPARTMENTS)

    for model in (Student, Teacher, AcademicMaterial):
        department_names.update(
            name.strip()
            for (name,) in db.session.query(model.department).filter(
                model.department.isnot(None),
                model.department != "",
            ).distinct().all()
            if name and name.strip()
        )

    for name in sorted(department_names, key=str.casefold):
        if name.casefold() not in existing_names:
            db.session.add(Department(name=name))
            existing_names.add(name.casefold())

    db.session.commit()


def get_departments():
    return Department.query.order_by(Department.name).all()


def selected_department_is_valid(name):
    return bool(name and Department.query.filter_by(name=name).first())


def department_is_in_use(name):
    return any([
        Student.query.filter_by(department=name).first(),
        Teacher.query.filter_by(department=name).first(),
        AcademicMaterial.query.filter_by(department=name).first(),
    ])


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


def get_current_teacher_profile():
    """Return the logged-in Teacher user and their Teacher profile record."""
    user = get_current_user_for_role("Teacher")
    if not user:
        return None, None

    teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
    if not teacher_profile:
        teacher_profile = Teacher(user_id=user.id)
        db.session.add(teacher_profile)
        db.session.commit()

    return user, teacher_profile


def get_current_user_for_role(role):
    if session.get("role") != role or "user_id" not in session:
        return None

    user = db.session.get(User, session["user_id"])
    if not user or user.role != role:
        session.clear()
        return None

    return user


def allowed_material_file(material_type, filename):
    rule = MATERIAL_UPLOAD_RULES.get(material_type)
    return (
        rule is not None
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in rule["extensions"]
    )


def material_rows(material_type, teacher_user_id):
    return [
        [
            material.title,
            material.subject or "Not set",
            material.uploaded_at.strftime("%d %b %Y"),
        ]
        for material in AcademicMaterial.query.filter_by(
            material_type=material_type,
            teacher_user_id=teacher_user_id,
        ).order_by(AcademicMaterial.uploaded_at.desc()).all()
    ]


def get_department_subjects(department):
    """Return real subjects available in a department, without hardcoding names."""
    if not department:
        return []

    teacher_subjects = [
        subject
        for (subject,) in db.session.query(Teacher.subject).filter(
            Teacher.department == department,
            Teacher.subject.isnot(None),
            Teacher.subject != "",
        ).distinct().all()
    ]
    material_subjects = [
        subject
        for (subject,) in db.session.query(AcademicMaterial.subject).filter(
            AcademicMaterial.department == department,
            AcademicMaterial.subject.isnot(None),
            AcademicMaterial.subject != "",
        ).distinct().all()
    ]
    return sorted(set(teacher_subjects + material_subjects), key=str.casefold)


def render_student_section(section_name):
    user, student_profile = get_current_student_profile()
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    title, icon, empty_message = STUDENT_SECTION_CONFIG[section_name]
    material_type = MATERIAL_TYPE_BY_SECTION.get(section_name)
    show_subject_filter = section_name in SUBJECT_FILTER_SECTIONS
    available_subjects = get_department_subjects(student_profile.department)
    selected_subject = request.args.get("subject", "").strip()
    if selected_subject not in available_subjects:
        selected_subject = ""

    academic_materials = []
    if material_type and student_profile.department:
        material_query = AcademicMaterial.query.filter_by(
            material_type=material_type,
            department=student_profile.department,
        )
        if show_subject_filter and selected_subject:
            material_query = material_query.filter_by(subject=selected_subject)
        academic_materials = material_query.order_by(
            AcademicMaterial.uploaded_at.desc()
        ).all()

    return render_template(
        "student_section.html",
        current_user=user,
        student_profile=student_profile,
        active_page=section_name,
        section_title=title,
        section_icon=icon,
        empty_message=empty_message,
        academic_materials=academic_materials,
        show_subject_filter=show_subject_filter,
        available_subjects=available_subjects,
        selected_subject=selected_subject,
        section_endpoint=f"student_{section_name}",
    )


def render_role_section(role, section_name, table_rows=None):
    user = get_current_user_for_role(role)
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    title, icon, headers, empty_message = ROLE_SECTION_CONFIG[role][section_name]
    return render_template(
        "dashboard_section.html",
        current_user=user,
        role=role,
        css_file=f"css/{role.lower()}.css",
        nav_items=ROLE_NAV_ITEMS[role],
        active_endpoint=request.endpoint,
        section_title=title,
        section_icon=icon,
        table_headers=headers,
        table_rows=table_rows or [],
        empty_message=empty_message,
    )


def get_parent_connected_students(user):
    connected_students = []
    connections = ParentStudentConnection.query.filter_by(
        parent_user_id=user.id
    ).all()
    for connection in connections:
        student_user = db.session.get(User, connection.student_user_id)
        profile = Student.query.filter_by(user_id=connection.student_user_id).first()
        if student_user and student_user.role == "Student" and profile:
            connected_students.append((student_user, profile))
    return connected_students


def get_parent_connected_student(user, student_user_id):
    if not student_user_id:
        return None

    connection = ParentStudentConnection.query.filter_by(
        parent_user_id=user.id,
        student_user_id=student_user_id,
    ).first()
    if not connection:
        return None

    student_user = db.session.get(User, student_user_id)
    profile = Student.query.filter_by(user_id=student_user_id).first()
    if not student_user or student_user.role != "Student" or not profile:
        return None
    return student_user, profile


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
        parent_email = request.form.get("parent_email", "").strip() or None
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

        if role in {"Student", "Teacher"} and not selected_department_is_valid(department):
            flash("Please select a valid department.")
            return redirect(url_for("register"))

        if role == "Student" and (not parent_email or "@" not in parent_email):
            flash("A valid parent email is required for Student registration.")
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
                department=department,
                parent_email=parent_email,
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
        "register.html",
        departments=get_departments(),
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

    assignment_query = AcademicMaterial.query.filter_by(
        material_type="Assignment",
        department=student_profile.department,
    )
    pending_assignment_count = assignment_query.count()
    today_schedule = WeeklySchedule.query.filter_by(
        student_user_id=user.id,
        day_of_week=datetime.today().weekday(),
    ).order_by(WeeklySchedule.start_time).all()
    available_subjects = get_department_subjects(student_profile.department)
    assignment_query = AcademicMaterial.query.filter_by(
        material_type="Assignment",
        department=student_profile.department,
    )
    if available_subjects:
        assignment_query = assignment_query.filter(
            AcademicMaterial.subject.in_(available_subjects)
        )
    recent_assignments = assignment_query.order_by(
        AcademicMaterial.uploaded_at.desc()
    ).limit(5).all()
    calendar_events = AcademicMaterial.query.filter_by(
        material_type="Academic Calendar",
        department=student_profile.department,
    ).order_by(AcademicMaterial.uploaded_at.desc()).all()
    today = datetime.today()

    return render_template(
        "student.html",
        current_user=user,
        student_profile=student_profile,
        pending_assignment_count=pending_assignment_count,
        attendance_percentage=None,
        overall_gpa=None,
        attendance_overview=[],
        grades_overview=[],
        today_schedule=today_schedule,
        recent_assignments=recent_assignments,
        calendar_events=calendar_events,
        calendar_year=today.year,
        calendar_month=today.strftime("%B"),
        month_grid=calendar_module.monthcalendar(today.year, today.month),
        today_day=today.day,
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

        department = request.form.get("department", "").strip()
        if not selected_department_is_valid(department):
            flash("Please select a valid department.")
            return redirect(url_for("edit_student_profile"))

        user.full_name = full_name
        user.email = email
        user.phone = request.form.get("phone", "").strip() or None
        profile.phone = user.phone
        profile.department = department
        profile.semester = semester
        profile.division = request.form.get("division", "").strip() or None
        db.session.commit()

        flash("Profile updated successfully!")
        return redirect(url_for("student_profile"))

    return render_template(
        "edit_student_profile.html",
        current_user=user,
        student_profile=profile,
        departments=get_departments(),
        active_page="profile"
    )


@app.route("/student/attendance")
def student_attendance():
    return render_student_section("attendance")


@app.route("/student/materials")
def student_materials():
    return render_student_section("materials")


@app.route("/student/timetable", methods=["GET", "POST"])
def student_timetable():
    user, profile = get_current_student_profile()
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    if request.method == "POST":
        values = {key: request.form.get(key, "").strip() for key in ("day_of_week", "start_time", "end_time", "subject", "room", "teacher", "class_type")}
        try:
            day = int(values["day_of_week"])
        except ValueError:
            day = -1
        if not 0 <= day <= 6 or not values["start_time"] or not values["end_time"] or not values["subject"]:
            flash("Day, time, and subject are required.")
            return redirect(url_for("student_timetable"))
        db.session.add(WeeklySchedule(student_user_id=user.id, day_of_week=day, **{key: values[key] for key in values if key != "day_of_week"}))
        db.session.commit()
        flash("Schedule saved successfully.")
        return redirect(url_for("student_timetable"))
    schedules = WeeklySchedule.query.filter_by(student_user_id=user.id).order_by(WeeklySchedule.day_of_week, WeeklySchedule.start_time).all()
    return render_template("student_timetable.html", current_user=user, student_profile=profile, schedules=schedules, active_page="timetable")


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
    return redirect(url_for("settings"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    role = session.get("role")
    user = get_current_user_for_role(role) if role in ROLE_DASHBOARD_ENDPOINTS else None
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "preferences":
            user.theme = request.form.get("theme", "light") if request.form.get("theme") in {"light", "dark"} else "light"
            user.notifications_enabled = request.form.get("notifications_enabled") == "on"
            user.accent_color = request.form.get("accent_color", "purple") if request.form.get("accent_color") in {"purple", "blue", "green"} else "purple"
            db.session.commit()
            flash("Settings saved successfully.")
        elif action == "password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")
            if not bcrypt.check_password_hash(user.password, current_password):
                flash("Current password is incorrect.")
            elif not new_password:
                flash("New password is required.")
            elif new_password != confirm_password:
                flash("New passwords do not match.")
            else:
                user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
                db.session.commit()
                flash("Password changed successfully.")
        return redirect(url_for("settings"))

    return render_template("settings.html", current_user=user, role=role, dashboard_endpoint=ROLE_DASHBOARD_ENDPOINTS[role])


@app.route("/teacher/settings")
@app.route("/parent/settings")
@app.route("/admin/settings")
def role_settings():
    return redirect(url_for("settings"))


# ==========================================
# TEACHER DASHBOARD
# ==========================================

@app.route("/teacher")
def teacher():
    user, teacher_profile = get_current_teacher_profile()
    if not user:
        flash("Access denied!")
        return redirect(
            url_for("login")
        )

    return render_template(
        "teacher.html",
        current_user=user,
        teacher_profile=teacher_profile
    )


@app.route("/teacher/profile")
def teacher_profile():
    user, profile = get_current_teacher_profile()
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    return render_template(
        "teacher_profile.html",
        current_user=user,
        teacher_profile=profile,
        active_page="profile",
    )


@app.route("/teacher/profile/edit", methods=["GET", "POST"])
def edit_teacher_profile():
    user, profile = get_current_teacher_profile()
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()

        if not full_name or not email:
            flash("Full name and email are required.")
            return redirect(url_for("edit_teacher_profile"))

        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id,
        ).first()
        if existing_email:
            flash("Email already registered!")
            return redirect(url_for("edit_teacher_profile"))

        department = request.form.get("department", "").strip()
        if not selected_department_is_valid(department):
            flash("Please select a valid department.")
            return redirect(url_for("edit_teacher_profile"))

        user.full_name = full_name
        user.email = email
        user.phone = request.form.get("phone", "").strip() or None
        profile.department = department
        profile.subject = request.form.get("subject", "").strip() or None
        db.session.commit()

        flash("Profile updated successfully!")
        return redirect(url_for("teacher_profile"))

    return render_template(
        "edit_teacher_profile.html",
        current_user=user,
        teacher_profile=profile,
        departments=get_departments(),
        active_page="profile",
    )


@app.route("/teacher/students")
def teacher_students():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
    profiles = Student.query.filter_by(
        department=teacher_profile.department
    ).all() if teacher_profile and teacher_profile.department else []
    rows = []
    for profile in profiles:
        student_user = db.session.get(User, profile.user_id)
        if student_user and student_user.role == "Student":
            rows.append([
                student_user.full_name,
                student_user.enrollment_no or "Not available",
                profile.department or "Not available",
                profile.semester or "Not available",
            ])
    return render_role_section("Teacher", "students", rows)


@app.route("/teacher/attendance")
def teacher_attendance():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    return render_role_section(
        "Teacher", "attendance", material_rows("Attendance", user.id)
    )


@app.route("/teacher/materials")
def teacher_materials():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    return render_role_section(
        "Teacher", "materials", material_rows("Study Material", user.id)
    )


@app.route("/teacher/assignments")
def teacher_assignments():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    return render_role_section(
        "Teacher", "assignments", material_rows("Assignment", user.id)
    )


@app.route("/teacher/manage-materials", methods=["GET", "POST"])
def manage_materials():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
    if not teacher_profile or not teacher_profile.department:
        flash("Set your department before managing materials.")
        return redirect(url_for("teacher"))

    if request.method == "POST":
        material_type = request.form.get("material_type", "")
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        subject = request.form.get("subject", "").strip()
        uploaded_file = request.files.get("material_file")

        if material_type not in MATERIAL_TYPES or not title:
            flash("Select a material type and enter a title.")
            return redirect(url_for("manage_materials"))

        upload_rule = MATERIAL_UPLOAD_RULES[material_type]
        if material_type in SUBJECT_MATERIAL_TYPES:
            teacher_subject = (teacher_profile.subject or "").strip()
            if not teacher_subject:
                flash("Set your subject in your profile before uploading this material.")
                return redirect(url_for("manage_materials"))
            if subject != teacher_subject:
                flash("Select your assigned subject for this material.")
                return redirect(url_for("manage_materials"))
        else:
            subject = None

        has_file = bool(uploaded_file and uploaded_file.filename)
        if upload_rule["description_required"] and not description:
            flash("A description is required for a notice.")
            return redirect(url_for("manage_materials"))

        if upload_rule["file_required"] and not has_file:
            flash(f"{upload_rule['file_label']} is required for {material_type}.")
            return redirect(url_for("manage_materials"))

        original_filename = None
        stored_filename = None
        saved_path = None
        if has_file:
            if not allowed_material_file(material_type, uploaded_file.filename):
                flash(
                    f"Unsupported file type. {material_type} accepts "
                    f"{upload_rule['file_label']}."
                )
                return redirect(url_for("manage_materials"))

            original_filename = secure_filename(uploaded_file.filename)
            stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
            os.makedirs(MATERIAL_UPLOAD_FOLDER, exist_ok=True)
            saved_path = os.path.join(MATERIAL_UPLOAD_FOLDER, stored_filename)
            uploaded_file.save(saved_path)

        material = AcademicMaterial(
            teacher_user_id=user.id,
            material_type=material_type,
            department=teacher_profile.department,
            subject=subject,
            title=title,
            description=description or None,
            original_filename=original_filename,
            stored_filename=stored_filename,
        )
        try:
            db.session.add(material)
            db.session.commit()
        except Exception:
            db.session.rollback()
            if saved_path and os.path.exists(saved_path):
                os.remove(saved_path)
            flash("Unable to save the material. Please try again.")
            return redirect(url_for("manage_materials"))

        flash("Material saved successfully.")
        return redirect(url_for("manage_materials"))

    materials = AcademicMaterial.query.filter_by(
        teacher_user_id=user.id
    ).order_by(AcademicMaterial.uploaded_at.desc()).all()
    return render_template(
        "manage_materials.html",
        current_user=user,
        teacher_profile=teacher_profile,
        material_types=sorted(MATERIAL_TYPES),
        material_upload_rules=MATERIAL_UPLOAD_RULES,
        teacher_subjects=[teacher_profile.subject] if teacher_profile.subject else [],
        materials=materials,
    )


@app.route("/materials/<int:material_id>/download")
def download_material(material_id):
    user_id = session.get("user_id")
    role = session.get("role")
    material = db.session.get(AcademicMaterial, material_id)
    if not user_id or material is None or not material.stored_filename:
        abort(404)

    if role == "Student":
        student_profile = Student.query.filter_by(user_id=user_id).first()
        permitted = bool(
            student_profile and student_profile.department == material.department
        )
    elif role == "Teacher":
        permitted = material.teacher_user_id == user_id
    elif role == "Parent":
        parent_user = db.session.get(User, user_id)
        permitted = bool(
            parent_user and any(
                student_profile.department == material.department
                for _, student_profile in get_parent_connected_students(parent_user)
            )
        )
    else:
        permitted = False

    if not permitted:
        abort(403)

    return send_from_directory(
        MATERIAL_UPLOAD_FOLDER,
        material.stored_filename,
        as_attachment=True,
        download_name=material.original_filename,
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

    connected_students = get_parent_connected_students(user)

    return render_template(
        "parent.html",
        current_user=user,
        connected_students=connected_students
    )


@app.route("/parent/connect-student", methods=["POST"])
def connect_parent_student():
    user = get_current_user_for_role("Parent")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    enrollment_no = request.form.get("enrollment_no", "").strip()
    student_user = User.query.filter_by(enrollment_no=enrollment_no).first()
    if not enrollment_no or not student_user or student_user.role != "Student":
        flash("Student enrollment number was not found.")
        return redirect(url_for("parent"))

    student_profile = Student.query.filter_by(user_id=student_user.id).first()
    parent_email = (user.email or "").strip().casefold()
    registered_parent_email = (
        (student_profile.parent_email or "").strip().casefold()
        if student_profile else ""
    )
    if not parent_email or parent_email != registered_parent_email:
        flash("This student is not registered with your parent email.")
        return redirect(url_for("parent"))

    existing_connection = ParentStudentConnection.query.filter_by(
        parent_user_id=user.id,
        student_user_id=student_user.id,
    ).first()
    if existing_connection:
        flash("This student is already connected to your account.")
        return redirect(url_for("parent"))

    db.session.add(ParentStudentConnection(
        parent_user_id=user.id,
        student_user_id=student_user.id,
    ))
    db.session.commit()
    flash("Student connected successfully.")
    return redirect(url_for("parent"))


@app.route("/parent/students")
def parent_students():
    user = get_current_user_for_role("Parent")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    rows = [
        [
            student_user.full_name,
            student_user.enrollment_no or "Not available",
            profile.department or "Not available",
            profile.semester or "Not available",
            profile.division or "Not available",
        ]
        for student_user, profile in get_parent_connected_students(user)
    ]
    return render_role_section("Parent", "students", rows)


def render_parent_academic_section(material_type, title, icon, empty_message):
    user = get_current_user_for_role("Parent")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    connected_students = get_parent_connected_students(user)
    requested_student_id = request.args.get("student_id", type=int)
    selected_student = get_parent_connected_student(user, requested_student_id)
    if requested_student_id and not selected_student:
        flash("You can only view data for a connected student.")
        return redirect(url_for("parent"))
    if not selected_student and connected_students:
        selected_student = connected_students[0]

    materials = []
    if selected_student:
        _, student_profile = selected_student
        materials = AcademicMaterial.query.filter_by(
            material_type=material_type,
            department=student_profile.department,
        ).order_by(AcademicMaterial.uploaded_at.desc()).all()

    return render_template(
        "parent_academic_section.html",
        current_user=user,
        connected_students=connected_students,
        selected_student=selected_student,
        materials=materials,
        section_title=title,
        section_icon=icon,
        empty_message=empty_message,
    )


@app.route("/parent/results")
def parent_results():
    return render_parent_academic_section(
        "Result", "Results", "fa-square-poll-vertical", "No data available."
    )


@app.route("/parent/attendance")
def parent_attendance():
    return render_parent_academic_section(
        "Attendance", "Attendance", "fa-user-check", "No data available."
    )


@app.route("/parent/calendar")
def parent_calendar():
    return render_parent_academic_section(
        "Academic Calendar", "Academic Calendar", "fa-calendar-week",
        "No data available.",
    )


@app.route("/parent/notices")
def parent_notices():
    return render_role_section("Parent", "notices")


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


def admin_user_rows(role, identifier_field):
    return [
        [
            user.full_name,
            getattr(user, identifier_field) or "Not available",
            user.email or "Not available",
            user.phone or "Not available",
        ]
        for user in User.query.filter_by(role=role).all()
    ]


@app.route("/admin/students")
def admin_students():
    return render_role_section("Admin", "students", admin_user_rows("Student", "enrollment_no"))


@app.route("/admin/teachers")
def admin_teachers():
    return render_role_section("Admin", "teachers", admin_user_rows("Teacher", "employee_id"))


@app.route("/admin/parents")
def admin_parents():
    return render_role_section("Admin", "parents", admin_user_rows("Parent", "parent_id"))


@app.route("/admin/departments", methods=["GET", "POST"])
def manage_departments():
    user = get_current_user_for_role("Admin")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            name = request.form.get("department_name", "").strip()
            if not name:
                flash("Department name is required.")
            elif len(name) > 100:
                flash("Department name must be 100 characters or fewer.")
            elif Department.query.filter(
                func.lower(Department.name) == name.casefold()
            ).first():
                flash("That department already exists.")
            else:
                db.session.add(Department(name=name))
                db.session.commit()
                flash("Department added successfully.")

        elif action == "remove":
            department = db.session.get(
                Department, request.form.get("department_id", type=int)
            )
            if not department:
                flash("Department not found.")
            elif department_is_in_use(department.name):
                flash("This department is in use and cannot be removed.")
            else:
                db.session.delete(department)
                db.session.commit()
                flash("Department removed successfully.")

        return redirect(url_for("manage_departments"))

    return render_template(
        "manage_departments.html",
        current_user=user,
        departments=get_departments(),
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
    ensure_academic_material_columns()
    seed_departments()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
