import os
import uuid
import calendar as calendar_module
from datetime import datetime, timedelta
import flask

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
from flask_login import LoginManager, current_user, login_user, logout_user
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
from models.notification import StudentNotification
from models.student_result import StudentResult
from models.student_final_result import StudentFinalResult
from models.subject import Subject
from models.teacher_subject_assignment import TeacherSubjectAssignment
from models.attendance import Attendance


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


@app.before_request
def restore_application_session():
    """Keep the existing role-based session in sync with Flask-Login."""
    if current_user.is_authenticated:
        session["user_id"] = current_user.id
        session["role"] = current_user.role


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
    "final_results": ("Final Result", "fa-file-certificate", "No final result documents uploaded."),
    "fees": ("Fees", "fa-wallet", "No fee information available."),
    "library": ("My Courses", "fa-book-open-reader", "No enrolled subjects available."),
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
FINAL_RESULT_UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "final_results")
FINAL_RESULT_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "webp"}

ROLE_NAV_ITEMS = {
    "Teacher": [
        ("teacher", "Dashboard", "fa-house"),
        ("teacher_profile", "Profile", "fa-circle-user"),
        ("teacher_students", "Students", "fa-users"),
        ("teacher_attendance", "Attendance", "fa-user-check"),
        ("teacher_previous_attendance", "Previous Attendance", "fa-clock-rotate-left"),
        ("teacher_materials", "Study Material", "fa-book"),
        ("teacher_assignments", "Assignments", "fa-file-lines"),
        ("teacher_lectures", "Manage Weekly Schedule", "fa-calendar-days"),
        ("manage_materials", "Manage Materials", "fa-folder-plus"),
        ("teacher_settings", "Settings", "fa-gear"),
    ],
    "Parent": [
        ("parent", "Dashboard", "fa-house"),
        ("parent_students", "My Students", "fa-user-graduate"),
        ("parent_results", "Results", "fa-square-poll-vertical"),
        ("parent_attendance", "Attendance", "fa-user-check"),
        ("parent_calendar", "Academic Calendar", "fa-calendar-week"),
        ("parent_notices", "Notices", "fa-bell"),
        ("parent_settings", "Settings", "fa-gear"),
    ],
    "Admin": [
        ("admin", "Dashboard", "fa-house"),
        ("manage_departments", "Departments", "fa-building"),
        ("admin_subject_assignments", "Subject Assignments", "fa-book"),
        ("admin_students", "Students", "fa-user-graduate"),
        ("admin_teachers", "Teachers", "fa-chalkboard-user"),
        ("admin_parents", "Parents", "fa-people-group"),
        ("admin_management", "Admin Management", "fa-user-shield"),
        ("admin_settings", "Settings", "fa-gear"),
    ],
}

ROLE_SECTION_CONFIG = {
    "Teacher": {
        "students": ("Students", "fa-users", ["Name", "Enrollment Number", "Department", "Semester"], "No students are assigned to your department."),
        "attendance": ("Attendance", "fa-user-check", ["Student", "Subject", "Date", "Status"], "No attendance records are available yet."),
        "materials": ("Study Material", "fa-book", ["Title", "Subject", "Uploaded On", "Download"], "You have not uploaded any study material yet."),
        "assignments": ("Assignments", "fa-file-lines", ["Assignment", "Subject", "Due Date", "Download"], "You have not created any assignments yet."),
        "lectures": ("Weekly Schedule", "fa-calendar-days", [], "No lectures scheduled yet."),
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


def ensure_weekly_schedule_columns():
    columns = {column["name"] for column in inspect(db.engine).get_columns("weekly_schedules")}
    if "department" not in columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE weekly_schedules ADD COLUMN department VARCHAR(100)"))


def ensure_student_result_columns():
    columns = {column["name"] for column in inspect(db.engine).get_columns("student_results")}
    if "out_of_marks" not in columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE student_results ADD COLUMN out_of_marks FLOAT NOT NULL DEFAULT 100"))
    if "is_internal" not in columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE student_results ADD COLUMN is_internal BOOLEAN NOT NULL DEFAULT 1"))


def ensure_teacher_subject_assignment_columns():
    columns = {column["name"] for column in inspect(db.engine).get_columns("teacher_subject_assignments")}
    with db.engine.begin() as connection:
        if "semester" not in columns:
            connection.execute(text("ALTER TABLE teacher_subject_assignments ADD COLUMN semester INTEGER"))
        if "division" not in columns:
            connection.execute(text("ALTER TABLE teacher_subject_assignments ADD COLUMN division VARCHAR(10)"))


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


def get_student_schedule_for_day(user_id, day_of_week=None):
    """Return one student's schedule entries for the requested weekday."""
    if day_of_week is None:
        day_of_week = datetime.today().weekday()
    return WeeklySchedule.query.filter(
        WeeklySchedule.student_user_id == user_id,
        WeeklySchedule.day_of_week == day_of_week,
    ).order_by(WeeklySchedule.start_time).all()


def create_material_notifications(material):
    """Notify eligible students once a teacher's material is committed."""
    teacher = db.session.get(User, material.teacher_user_id)
    if not teacher:
        return
    students = Student.query.join(User, User.id == Student.user_id).filter(
        User.role == "Student",
        Student.department == material.department,
    ).all()
    for profile in students:
        subjects = get_department_subjects(profile.department)
        if material.subject and subjects and material.subject not in subjects:
            continue
        exists = StudentNotification.query.filter_by(
            student_user_id=profile.user_id,
            material_id=material.id,
        ).first()
        if not exists:
            db.session.add(StudentNotification(
                student_user_id=profile.user_id,
                material_id=material.id,
                material_type=material.material_type,
                title=material.title,
                teacher_name=teacher.full_name,
                subject=material.subject,
                department=material.department,
                created_at=material.uploaded_at,
            ))
    db.session.commit()


def get_attendance_summary(student_user_id, subject_name=None):
    """Return subject-wise attendance and the overall percentage from records."""
    records = Attendance.query.filter_by(student_user_id=student_user_id).join(Subject).order_by(Subject.name, Attendance.date).all()
    if subject_name:
        records = [record for record in records if record.subject and record.subject.name == subject_name]
    grouped = {}
    for record in records:
        item = grouped.setdefault(record.subject_id, {
            "subject": record.subject.name if record.subject else "Subject unavailable",
            "present": 0,
            "total": 0,
        })
        item["total"] += 1
        if record.status == "Present":
            item["present"] += 1
    summaries = []
    for item in grouped.values():
        item["percentage"] = round(item["present"] / item["total"] * 100, 2) if item["total"] else 0
        summaries.append(item)
    total = sum(item["total"] for item in summaries)
    present = sum(item["present"] for item in summaries)
    overall = round(present / total * 100, 2) if total else None
    return summaries, overall


def render_student_section(section_name):
    user, student_profile = get_current_student_profile()
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    title, icon, empty_message = STUDENT_SECTION_CONFIG[section_name]
    material_type = MATERIAL_TYPE_BY_SECTION.get(section_name)
    show_subject_filter = section_name in SUBJECT_FILTER_SECTIONS
    assigned_subjects = TeacherSubjectAssignment.query.join(Subject).filter(
        Subject.department == student_profile.department,
        TeacherSubjectAssignment.semester == student_profile.semester,
        TeacherSubjectAssignment.division == student_profile.division,
    ).all()
    available_subjects = sorted({assignment.subject.name for assignment in assigned_subjects if assignment.subject}, key=str.casefold)
    selected_subject = request.args.get("subject", "").strip()
    if selected_subject not in available_subjects:
        selected_subject = ""

    academic_materials = []
    notifications = []
    student_results = []
    final_result_documents = []
    course_rows = []
    schedules = []
    attendance_summary = []
    internal_average = None
    if material_type and student_profile.department:
        material_query = AcademicMaterial.query.filter_by(
            material_type=material_type,
            department=student_profile.department,
        )
        if available_subjects:
            material_query = material_query.filter(AcademicMaterial.subject.in_(available_subjects))
        else:
            material_query = material_query.filter(AcademicMaterial.id == -1)
        if show_subject_filter and selected_subject:
            material_query = material_query.filter_by(subject=selected_subject)
        academic_materials = material_query.order_by(
            AcademicMaterial.uploaded_at.desc()
        ).all()
    if section_name == "notices":
        notifications = StudentNotification.query.filter_by(
            student_user_id=user.id
        ).order_by(StudentNotification.created_at.desc()).all()
    if section_name == "results":
        student_results = StudentResult.query.filter_by(
            student_user_id=user.id
        ).order_by(StudentResult.updated_at.desc()).all()
        if selected_subject:
            student_results = [result for result in student_results if result.subject == selected_subject]
        else:
            student_results = [result for result in student_results if result.subject in available_subjects]
        percentages = []
        for result in student_results:
            try:
                if result.is_internal and result.out_of_marks and float(result.out_of_marks) > 0:
                    percentages.append(float(result.marks_grade) / float(result.out_of_marks) * 100)
            except (TypeError, ValueError):
                continue
        if percentages:
            internal_average = round(sum(percentages) / len(percentages), 2)
    if section_name == "attendance":
        attendance_summary, _ = get_attendance_summary(user.id, selected_subject)
        if not selected_subject:
            attendance_summary = [item for item in attendance_summary if item["subject"] in available_subjects]
    if section_name == "final_results":
        final_result_documents = StudentFinalResult.query.filter_by(student_user_id=user.id).order_by(StudentFinalResult.uploaded_at.desc()).all()
    if section_name == "library":
        assignments = TeacherSubjectAssignment.query.join(Subject).join(
            User, User.id == TeacherSubjectAssignment.teacher_user_id
        ).filter(
            Subject.department == student_profile.department,
            TeacherSubjectAssignment.semester == student_profile.semester,
            TeacherSubjectAssignment.division == student_profile.division,
            User.role == "Teacher",
        ).order_by(Subject.name, User.full_name).all()
        grouped = {}
        for assignment in assignments:
            key = assignment.subject.id
            course = grouped.setdefault(key, {
                "subject": assignment.subject.name,
                "department": assignment.subject.department,
                "semester": assignment.semester,
                "teachers": [],
            })
            if assignment.teacher and assignment.teacher.full_name not in course["teachers"]:
                course["teachers"].append(assignment.teacher.full_name)
        for course in grouped.values():
            course["teacher"] = ", ".join(course.pop("teachers")) or "Not assigned"
            course_rows.append(course)
    if section_name == "timetable":
        schedules = WeeklySchedule.query.filter_by(
            student_user_id=user.id
        ).order_by(WeeklySchedule.day_of_week, WeeklySchedule.start_time).all()

    return render_template(
        "student_section.html",
        current_user=user,
        student_profile=student_profile,
        active_page=section_name,
        section_title=title,
        section_name=section_name,
        section_icon=icon,
        empty_message=empty_message,
        academic_materials=academic_materials,
        show_subject_filter=show_subject_filter,
        available_subjects=available_subjects,
        selected_subject=selected_subject,
        section_endpoint=f"student_{section_name}",
        notifications=notifications,
        student_results=student_results,
        internal_average=internal_average,
        final_result_documents=final_result_documents,
        course_rows=course_rows,
        schedules=schedules,
        attendance_summary=attendance_summary,
    )


def render_role_section(role, section_name, table_rows=None, row_ids=None, search_query="", material_ids=None):
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
        section_name=section_name,
        section_icon=icon,
        table_headers=headers,
        table_rows=table_rows or [],
        row_ids=row_ids or [],
        material_ids=material_ids or [],
        search_query=search_query,
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

    if request.method == "GET" and current_user.is_authenticated:
        return redirect(url_for(ROLE_DASHBOARD_ENDPOINTS[current_user.role]))

    if request.method == "POST":

        # Clear any prior Flask-Login state (including an old remember cookie)
        # before starting this login attempt.
        logout_user()
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
            remember = request.form.get("remember_me") == "on"
            login_user(user, remember=remember)
            session["user_id"] = user.id
            session["role"] = user.role
            return redirect(url_for(ROLE_DASHBOARD_ENDPOINTS[user.role]))

        flash("Invalid ID or Password!")

        return redirect(
            url_for("login")
        )

    return render_template("login.html")


@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")


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

        if role == "Student" and not selected_department_is_valid(department):
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
    today = datetime.today()
    today_schedule = get_student_schedule_for_day(user.id, today.weekday())
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
    unread_notification_count = StudentNotification.query.filter_by(
        student_user_id=user.id,
    ).filter(StudentNotification.read_at.is_(None)).count()
    today_lectures = WeeklySchedule.query.filter(
        WeeklySchedule.day_of_week == datetime.today().weekday(),
        WeeklySchedule.student_user_id == user.id,
        func.lower(func.trim(WeeklySchedule.teacher)) == user.full_name.strip().lower(),
    ).order_by(WeeklySchedule.start_time).all()
    attendance_overall = get_attendance_summary(user.id)[1]
    week_start = today.date() - timedelta(days=today.weekday())
    weekly_attendance = []
    for day_offset, label in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")):
        day = week_start + timedelta(days=day_offset)
        attended = Attendance.query.filter_by(
            student_user_id=user.id, date=day, status="Present"
        ).count()
        weekly_attendance.append({"label": label, "attended": attended})
    weekly_attendance_max = max((point["attended"] for point in weekly_attendance), default=0)
    internal_results = StudentResult.query.filter_by(student_user_id=user.id, is_internal=True).all()
    internal_percentages = []
    for result in internal_results:
        try:
            if result.out_of_marks and float(result.out_of_marks) > 0:
                internal_percentages.append(float(result.marks_grade) / float(result.out_of_marks) * 100)
        except (TypeError, ValueError):
            continue
    internal_average = round(sum(internal_percentages) / len(internal_percentages), 2) if internal_percentages else None
    recent_results = []
    for result in StudentResult.query.filter_by(student_user_id=user.id).order_by(StudentResult.updated_at.desc()).limit(5).all():
        percentage = None
        try:
            if result.out_of_marks and float(result.out_of_marks) > 0:
                percentage = round(float(result.marks_grade) / float(result.out_of_marks) * 100, 2)
        except (TypeError, ValueError):
            pass
        recent_results.append({
            "subject": result.subject,
            "exam": result.exam,
            "marks": result.marks_grade,
            "out_of_marks": result.out_of_marks,
            "percentage": percentage,
        })

    return render_template(
        "student.html",
        current_user=user,
        student_profile=student_profile,
        pending_assignment_count=pending_assignment_count,
        attendance_percentage=attendance_overall,
        overall_gpa=f"{internal_average}%" if internal_average is not None else None,
        attendance_overview=weekly_attendance,
        weekly_attendance_max=weekly_attendance_max,
        grades_overview=[],
        recent_results=recent_results,
        today_schedule=today_schedule,
        recent_assignments=recent_assignments,
        calendar_events=calendar_events,
        calendar_year=today.year,
        calendar_month=today.strftime("%B"),
        month_grid=calendar_module.monthcalendar(today.year, today.month),
        today_day=today.day,
        unread_notification_count=unread_notification_count,
        today_lectures=today_lectures,
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
        if request.form.get("action") == "delete":
            lecture = WeeklySchedule.query.filter_by(
                id=request.form.get("lecture_id", type=int),
                student_user_id=user.id,
            ).first()
            if not lecture:
                flash("Schedule entry not found.")
            else:
                db.session.delete(lecture)
                db.session.commit()
                flash("Lecture removed successfully.")
            return redirect(url_for("student_timetable"))
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


@app.route("/student/final-results", methods=["GET", "POST"])
def student_final_results():
    user = get_current_user_for_role("Student")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    if request.method == "POST":
        uploaded = request.files.get("final_result_file")
        if not uploaded or not uploaded.filename or "." not in uploaded.filename or uploaded.filename.rsplit(".", 1)[1].lower() not in FINAL_RESULT_EXTENSIONS:
            flash("Please upload a PDF, JPG, JPEG, PNG, or WEBP file.")
            return redirect(url_for("student_final_results"))
        original = secure_filename(uploaded.filename)
        stored = f"{uuid.uuid4().hex}_{original}"
        os.makedirs(FINAL_RESULT_UPLOAD_FOLDER, exist_ok=True)
        uploaded.save(os.path.join(FINAL_RESULT_UPLOAD_FOLDER, stored))
        document_id = request.form.get("document_id", type=int)
        if document_id:
            document = StudentFinalResult.query.filter_by(id=document_id, student_user_id=user.id).first_or_404()
            old_path = os.path.join(FINAL_RESULT_UPLOAD_FOLDER, document.stored_filename)
            document.original_filename, document.stored_filename, document.uploaded_at = original, stored, datetime.utcnow()
            if os.path.exists(old_path):
                os.remove(old_path)
        else:
            db.session.add(StudentFinalResult(student_user_id=user.id, original_filename=original, stored_filename=stored))
        db.session.commit()
        flash("Final result document uploaded successfully.")
        return redirect(url_for("student_final_results"))
    return render_student_section("final_results")


@app.route("/student/final-results/<int:document_id>/download")
def download_student_final_result(document_id):
    user = get_current_user_for_role("Student")
    document = StudentFinalResult.query.filter_by(id=document_id, student_user_id=user.id if user else -1).first_or_404()
    return send_from_directory(FINAL_RESULT_UPLOAD_FOLDER, document.stored_filename, as_attachment=False, download_name=document.original_filename)


@app.route("/student/final-results/<int:document_id>/delete", methods=["POST"])
def delete_student_final_result(document_id):
    user = get_current_user_for_role("Student")
    if not user:
        return redirect(url_for("login"))
    document = StudentFinalResult.query.filter_by(id=document_id, student_user_id=user.id).first_or_404()
    path = os.path.join(FINAL_RESULT_UPLOAD_FOLDER, document.stored_filename)
    db.session.delete(document)
    db.session.commit()
    if os.path.exists(path):
        os.remove(path)
    flash("Final result document deleted.")
    return redirect(url_for("student_final_results"))


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
def teacher_settings():
    return redirect(url_for("settings"))


@app.route("/parent/settings")
def parent_settings():
    return redirect(url_for("settings"))


@app.route("/admin/settings")
def admin_settings():
    return redirect(url_for("settings"))


# ==========================================
# TEACHER DASHBOARD
# ==========================================

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    user, teacher_profile = get_current_teacher_profile()
    if not user:
        flash("Access denied!")
        return redirect(
            url_for("login")
        )

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        start_time = request.form.get("start_time", "").strip()
        end_time = request.form.get("end_time", "").strip()
        if not subject or not start_time or not end_time:
            flash("Subject, start time, and end time are required.")
            return redirect(url_for("teacher"))
        db.session.add(WeeklySchedule(
            student_user_id=user.id,
            day_of_week=datetime.today().weekday(),
            start_time=start_time,
            end_time=end_time,
            subject=subject,
            room=request.form.get("room", "").strip() or None,
            teacher=user.full_name,
        ))
        db.session.commit()
        flash("Today's lecture added successfully.")
        return redirect(url_for("teacher"))

    today = datetime.today()
    assigned_subject_ids = {
        assignment.subject_id
        for assignment in TeacherSubjectAssignment.query.filter_by(
            teacher_user_id=user.id
        ).all()
    }
    today_lectures = WeeklySchedule.query.filter_by(
        student_user_id=user.id,
        teacher=user.full_name,
        day_of_week=today.weekday(),
    ).order_by(WeeklySchedule.start_time).all()

    # Build the dashboard summary from today's scheduled lectures and the
    # lecture-wise attendance records already saved by this teacher.
    lecture_keys = {
        (lecture.subject.strip().casefold(), lecture.start_time, lecture.end_time)
        for lecture in today_lectures
        if lecture.subject and lecture.start_time and lecture.end_time
    }
    today_records = Attendance.query.filter_by(
        teacher_user_id=user.id, date=today.date()
    ).all()
    session_records = {}
    for record in today_records:
        subject_name = record.subject.name if record.subject else ""
        key = (subject_name.strip().casefold(), record.start_time, record.end_time)
        if key in lecture_keys:
            session_records.setdefault(key, []).append(record)
    marked_count = len(session_records)
    attendance_percentages = [
        (sum(record.status == "Present" for record in records) / len(records)) * 100
        for records in session_records.values() if records
    ]
    attendance_summary = {
        "today_lectures": len(today_lectures),
        "attendance_marked": marked_count,
        "pending": max(len(today_lectures) - marked_count, 0),
        "average_present": round(sum(attendance_percentages) / len(attendance_percentages)) if attendance_percentages else None,
        "lectures": [
            {
                "subject": lecture.subject,
                "start_time": lecture.start_time,
                "end_time": lecture.end_time,
                "percentage": (
                    round(
                        sum(record.status == "Present" for record in session_records.get(
                            (lecture.subject.strip().casefold(), lecture.start_time, lecture.end_time), []
                        ))
                        / len(session_records.get(
                            (lecture.subject.strip().casefold(), lecture.start_time, lecture.end_time), []
                        )) * 100
                    )
                    if session_records.get((lecture.subject.strip().casefold(), lecture.start_time, lecture.end_time))
                    else None
                ),
            }
            for lecture in today_lectures
        ],
    }

    week_start = today.date() - timedelta(days=today.weekday())
    week_records = Attendance.query.filter(
        Attendance.teacher_user_id == user.id,
        Attendance.subject_id.in_(assigned_subject_ids) if assigned_subject_ids else Attendance.id == -1,
        Attendance.date >= week_start,
        Attendance.date <= today.date(),
    ).order_by(Attendance.id.desc()).all()
    # Keep the newest row for each lecture/student combination if legacy data
    # contains duplicates.
    unique_week_records = []
    seen_records = set()
    for record in week_records:
        key = (record.student_user_id, record.subject_id, record.date, record.start_time, record.end_time)
        if key not in seen_records:
            seen_records.add(key)
            unique_week_records.append(record)
    daily_records = {}
    for record in unique_week_records:
        daily_records.setdefault(record.date, []).append(record)
    attendance_analytics = []
    for day_offset in range(7):
        day = week_start + timedelta(days=day_offset)
        records = daily_records.get(day, [])
        attendance_analytics.append({
            "label": day.strftime("%a"),
            "percentage": round(sum(r.status == "Present" for r in records) / len(records) * 100, 1) if records else 0,
        })
    total_week_records = len(unique_week_records)
    week_present = sum(record.status == "Present" for record in unique_week_records)
    average_week_attendance = round(week_present / total_week_records * 100, 1) if total_week_records else None

    return render_template(
        "teacher.html",
        current_user=user,
        teacher_profile=teacher_profile,
        attendance_analytics=attendance_analytics,
        average_week_attendance=average_week_attendance,
        attendance_summary=attendance_summary,
        today_lectures=today_lectures,
        recent_uploads=AcademicMaterial.query.filter_by(
            teacher_user_id=user.id
        ).order_by(AcademicMaterial.uploaded_at.desc()).limit(5).all(),
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
        nav_items=ROLE_NAV_ITEMS["Teacher"],
        active_endpoint="teacher_profile",
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

        user.full_name = full_name
        user.email = email
        user.phone = request.form.get("phone", "").strip() or None
        profile.subject = request.form.get("subject", "").strip() or None
        db.session.commit()

        flash("Profile updated successfully!")
        return redirect(url_for("teacher_profile"))

    return render_template(
        "edit_teacher_profile.html",
        current_user=user,
        teacher_profile=profile,
        active_page="profile",
    )


@app.route("/teacher/students")
def teacher_students():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
    base_query = Student.query.filter_by(department=teacher_profile.department) if teacher_profile and teacher_profile.department else Student.query.filter(Student.id == -1)
    semester_values = list(range(1, 9))
    department_values = [department.name for department in Department.query.order_by(Department.name).all()]
    selected_semester = request.args.get("semester", "").strip()
    selected_department = request.args.get("department", "").strip()
    if selected_semester and selected_semester.isdigit():
        base_query = base_query.filter(Student.semester == int(selected_semester))
    else:
        selected_semester = ""
    if selected_department in department_values:
        base_query = Student.query.filter(Student.department == selected_department)
        if selected_semester:
            base_query = base_query.filter(Student.semester == int(selected_semester))
    else:
        selected_department = ""
    profiles = base_query.all()
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
    return render_template("dashboard_section.html", current_user=user, role="Teacher", css_file="css/teacher.css", nav_items=ROLE_NAV_ITEMS["Teacher"], active_endpoint=request.endpoint, section_title="Students", section_name="students", section_icon="fa-users", table_headers=ROLE_SECTION_CONFIG["Teacher"]["students"][2], table_rows=rows, empty_message=ROLE_SECTION_CONFIG["Teacher"]["students"][3], student_semesters=semester_values, student_departments=department_values, selected_semester=selected_semester, selected_department=selected_department)


@app.route("/teacher/previous-attendance", methods=["GET", "POST"])
def teacher_previous_attendance():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    assignments = TeacherSubjectAssignment.query.join(Subject).filter(
        TeacherSubjectAssignment.teacher_user_id == user.id
    ).all()
    departments = sorted({a.subject.department for a in assignments}, key=str.casefold)
    selected_department = request.values.get("department", "").strip()
    selected_semester = request.values.get("semester", "").strip()
    selected_division = request.values.get("division", "").strip().upper()
    selected_subject_id = request.values.get("subject_id", type=int)
    selected_date = request.values.get("attendance_date", "")
    selected_start = request.values.get("start_time", "")
    selected_end = request.values.get("end_time", "")
    load = request.values.get("load") == "1"
    valid_semester = selected_semester.isdigit() and int(selected_semester) in range(1, 9)
    valid_division = selected_division in {"A", "B", "C"}
    filtered = [a for a in assignments if
                (not selected_department or a.subject.department == selected_department) and
                (not selected_semester or (valid_semester and a.semester == int(selected_semester))) and
                (not selected_division or (valid_division and a.division == selected_division))]
    subject_options = sorted({a.subject.id: a.subject for a in filtered}.values(), key=lambda s: s.name.casefold())
    selected_assignment = next((a for a in filtered if a.subject_id == selected_subject_id), None)
    attendance_records = []

    if request.method == "POST" and request.form.get("action") == "edit":
        record = Attendance.query.filter_by(
            id=request.form.get("record_id", type=int), teacher_user_id=user.id
        ).first_or_404()
        status = request.form.get("status", "")
        if status not in {"Present", "Absent"}:
            flash("Select a valid attendance status.")
        else:
            record.status = status
            db.session.commit()
            flash("Attendance updated successfully.")
        return redirect(url_for("teacher_previous_attendance", department=selected_department,
                                semester=selected_semester, division=selected_division,
                                subject_id=selected_subject_id, attendance_date=selected_date,
                                start_time=selected_start, end_time=selected_end, load=1))

    lecture_date = None
    if load and selected_assignment and selected_date and selected_start and selected_end:
        try:
            lecture_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            lecture_date = None
        if lecture_date:
            attendance_records = Attendance.query.filter_by(
                teacher_user_id=user.id, subject_id=selected_assignment.subject_id,
                date=lecture_date, start_time=selected_start, end_time=selected_end
            ).order_by(Attendance.student_user_id).all()

    return render_template("teacher_previous_attendance.html", current_user=user, role="Teacher",
        nav_items=ROLE_NAV_ITEMS["Teacher"], active_endpoint="teacher_previous_attendance",
        departments=departments, semesters=range(1, 9), divisions=("A", "B", "C"),
        subject_options=subject_options, selected_department=selected_department,
        selected_semester=selected_semester, selected_division=selected_division,
        selected_subject_id=selected_subject_id, selected_date=selected_date,
        selected_start=selected_start, selected_end=selected_end, load=load,
        selected_assignment=selected_assignment, attendance_records=attendance_records)


@app.route("/teacher/attendance", methods=["GET", "POST"])
def teacher_attendance():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    teacher_assignments = TeacherSubjectAssignment.query.join(Subject).filter(
        TeacherSubjectAssignment.teacher_user_id == user.id
    ).all()
    department_values = sorted({a.subject.department for a in teacher_assignments}, key=str.casefold)
    selected_department = request.values.get("department", "").strip()
    selected_semester = request.values.get("semester", "").strip()
    selected_division = request.values.get("division", "").strip().upper()
    selected_subject_id = request.values.get("subject_id", type=int)
    selected_date = request.values.get("attendance_date", datetime.today().strftime("%Y-%m-%d"))
    date_filter_requested = bool(request.values.get("attendance_date"))
    selected_start = request.values.get("start_time", "")
    selected_end = request.values.get("end_time", "")
    load_students = request.values.get("load") == "1"
    review_requested = request.values.get("review") == "1"

    valid_semester = selected_semester.isdigit() and int(selected_semester) in range(1, 9)
    valid_division = selected_division in {"A", "B", "C"}
    filtered_assignments = [
        assignment for assignment in teacher_assignments
        if (not selected_department or assignment.subject.department == selected_department)
        and (not selected_semester or (valid_semester and assignment.semester == int(selected_semester)))
        and (not selected_division or (valid_division and assignment.division == selected_division))
    ]
    subject_options = sorted(
        {assignment.subject.id: assignment.subject for assignment in filtered_assignments}.values(),
        key=lambda subject: subject.name.casefold(),
    )
    selected_assignment = next(
        (assignment for assignment in filtered_assignments if assignment.subject_id == selected_subject_id),
        None,
    )
    review_subject_ids = {assignment.subject_id for assignment in filtered_assignments}
    attendance_records = []

    if request.method == "POST" and request.form.get("action") == "edit":
        record = Attendance.query.filter_by(
            id=request.form.get("record_id", type=int),
            teacher_user_id=user.id,
        ).first_or_404()
        status = request.form.get("status", "")
        if status not in {"Present", "Absent"}:
            flash("Select a valid attendance status.")
        else:
            record.status = status
            db.session.commit()
            flash("Attendance updated successfully.")
        return redirect(url_for(
            "teacher_attendance",
            department=selected_department,
            semester=selected_semester,
            division=selected_division,
            subject_id=selected_subject_id,
            attendance_date=selected_date,
            start_time=selected_start,
            end_time=selected_end,
            review=1,
        ))

    students = []
    if load_students and selected_assignment and valid_semester and valid_division and selected_department:
        students = [
            (db.session.get(User, profile.user_id), profile)
            for profile in Student.query.filter_by(
                department=selected_department,
                semester=int(selected_semester),
                division=selected_division,
            ).order_by(Student.user_id).all()
        ]
        students = [(student_user, profile) for student_user, profile in students if student_user and student_user.role == "Student"]

    if request.method == "POST":
        # Attendance is posted through the same section form; validate every
        # relationship again so a teacher cannot submit another teacher's subject.
        if not selected_assignment or not selected_department or not valid_semester or not valid_division:
            flash("Select a valid assigned subject, department, semester, and division.")
        elif not selected_date or not selected_start or not selected_end:
            flash("Date, start time, and end time are required.")
        else:
            try:
                lecture_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            except ValueError:
                lecture_date = None
            if lecture_date is None:
                flash("Select a valid lecture date.")
            elif selected_end <= selected_start:
                flash("End time must be after start time.")
            else:
                student_ids = {student_user.id for student_user, _ in students}
                submitted_ids = set()
                for key, status in request.form.items():
                    if not key.startswith("status_") or status not in {"Present", "Absent"}:
                        continue
                    try:
                        student_id = int(key.removeprefix("status_"))
                    except ValueError:
                        continue
                    if student_id not in student_ids:
                        continue
                    submitted_ids.add(student_id)
                    record = Attendance.query.filter_by(
                        student_user_id=student_id,
                        teacher_user_id=user.id,
                        subject_id=selected_assignment.subject_id,
                        date=lecture_date,
                        start_time=selected_start,
                        end_time=selected_end,
                    ).first()
                    if record is None:
                        record = Attendance(
                            student_user_id=student_id,
                            teacher_user_id=user.id,
                            subject_id=selected_assignment.subject_id,
                            date=lecture_date,
                            start_time=selected_start,
                            end_time=selected_end,
                        )
                        db.session.add(record)
                    record.status = status
                if submitted_ids != student_ids:
                    flash("Mark Present or Absent for every listed student.")
                else:
                    db.session.commit()
                    flash("Attendance saved successfully.")
        return redirect(url_for(
            "teacher_attendance",
            department=selected_department,
            semester=selected_semester,
            division=selected_division,
            subject_id=selected_subject_id,
            attendance_date=selected_date,
            start_time=selected_start,
            end_time=selected_end,
        ))

    if review_requested and review_subject_ids and selected_assignment and selected_date and selected_start and selected_end:
        attendance_query = Attendance.query.filter(
            Attendance.teacher_user_id == user.id,
            Attendance.subject_id.in_(review_subject_ids),
        )
        if date_filter_requested:
            try:
                review_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
                attendance_query = attendance_query.filter(Attendance.date == review_date)
            except ValueError:
                pass
        attendance_query = attendance_query.filter(
            Attendance.start_time == selected_start,
            Attendance.end_time == selected_end,
        )
        attendance_records = attendance_query.order_by(
            Attendance.date.desc(), Attendance.start_time, Attendance.id
        ).all()

    return render_template(
        "teacher_attendance.html",
        current_user=user,
        role="Teacher",
        nav_items=ROLE_NAV_ITEMS["Teacher"],
        active_endpoint="teacher_attendance",
        departments=department_values,
        semesters=range(1, 9),
        divisions=("A", "B", "C"),
        subject_options=subject_options,
        students=students,
        selected_department=selected_department,
        selected_semester=selected_semester,
        selected_division=selected_division,
        selected_subject_id=selected_subject_id,
        selected_date=selected_date,
        selected_start=selected_start,
        selected_end=selected_end,
        load_students=load_students,
        attendance_records=attendance_records,
        review_requested=review_requested,
    )


@app.route("/teacher/materials")
def teacher_materials():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    materials = AcademicMaterial.query.filter_by(
        material_type="Study Material", teacher_user_id=user.id
    ).order_by(AcademicMaterial.uploaded_at.desc()).all()
    return render_role_section(
        "Teacher", "materials", material_rows("Study Material", user.id),
        material_ids=[material.id for material in materials],
    )


@app.route("/teacher/assignments")
def teacher_assignments():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    assignments = AcademicMaterial.query.filter_by(
        material_type="Assignment", teacher_user_id=user.id
    ).order_by(AcademicMaterial.uploaded_at.desc()).all()
    return render_role_section(
        "Teacher", "assignments", material_rows("Assignment", user.id),
        material_ids=[assignment.id for assignment in assignments],
    )


@app.route("/teacher/manage-materials", methods=["GET", "POST"])
def manage_materials():
    user = get_current_user_for_role("Teacher")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    # A newly registered teacher has a profile row, but may not have a
    # department or subject assignment yet.  Those are managed separately by
    # the admin, so they must not prevent the Manage Materials section from
    # opening.
    teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
    if not teacher_profile:
        teacher_profile = Teacher(user_id=user.id)
        db.session.add(teacher_profile)
        db.session.commit()

    result_department = request.args.get("result_department", "").strip()
    result_semester = request.args.get("result_semester", "").strip()
    result_division = request.args.get("result_division", "").strip()
    result_subject = request.args.get("result_subject", "").strip()
    result_exam = request.args.get("result_exam", "").strip()
    result_departments = [d.name for d in Department.query.order_by(Department.name).all()]
    result_semesters = list(range(1, 9))
    result_divisions = [v for (v,) in Student.query.with_entities(Student.division).filter(Student.division.isnot(None), Student.division != "").distinct().order_by(Student.division).all()]
    result_subjects = get_department_subjects(result_department or teacher_profile.department)
    result_query = Student.query
    if result_department in result_departments:
        result_query = result_query.filter(Student.department == result_department)
    else:
        result_department = ""
    if result_semester.isdigit() and int(result_semester) in result_semesters:
        result_query = result_query.filter(Student.semester == int(result_semester))
    else:
        result_semester = ""
    if result_division in result_divisions:
        result_query = result_query.filter(Student.division == result_division)
    else:
        result_division = ""
    if result_subject:
        enrolled_ids = []
        if "student_subject_enrollments" in inspect(db.engine).get_table_names() and "subjects" in inspect(db.engine).get_table_names():
            enrolled_ids = [row[0] for row in db.session.execute(text("SELECT student_user_id FROM student_subject_enrollments e JOIN subjects s ON s.id = e.subject_id WHERE s.name = :subject"), {"subject": result_subject}).all()]
        if enrolled_ids:
            result_query = result_query.filter(Student.user_id.in_(enrolled_ids))
    result_students = [(profile, student_user) for profile in result_query.all() if (student_user := db.session.get(User, profile.user_id)) is not None]
    existing_results = {}
    if result_subject and result_exam:
        existing_results = {r.student.enrollment_no: r.marks_grade for r in StudentResult.query.filter_by(subject=result_subject, exam=result_exam).all() if r.student and r.student.enrollment_no}
    existing_out_of_marks = next((r.out_of_marks for r in StudentResult.query.filter_by(subject=result_subject, exam=result_exam).all()), None) if result_subject and result_exam else None
    existing_is_internal = next((r.is_internal for r in StudentResult.query.filter_by(subject=result_subject, exam=result_exam).all()), True) if result_subject and result_exam else True

    if request.method == "POST":
        if request.form.get("action") == "delete_material":
            material = AcademicMaterial.query.filter_by(
                id=request.form.get("material_id", type=int),
                teacher_user_id=user.id,
            ).first()
            if not material:
                flash("Material not found or you do not have permission to delete it.")
            else:
                stored_path = os.path.join(MATERIAL_UPLOAD_FOLDER, material.stored_filename) if material.stored_filename else None
                db.session.delete(material)
                db.session.commit()
                if stored_path and os.path.exists(stored_path):
                    os.remove(stored_path)
                flash("Material deleted successfully.")
            return redirect(url_for("manage_materials"))
        if request.form.get("action") == "save_results":
            subject = request.form.get("result_subject", "").strip()
            exam = request.form.get("result_exam", "").strip()
            try:
                out_of_marks = float(request.form.get("out_of_marks", ""))
            except (TypeError, ValueError):
                out_of_marks = 0
            if not subject or not exam or out_of_marks <= 0:
                flash("Subject, Exam/Assessment, and a valid Out of Marks value are required.")
                return redirect(url_for("manage_materials"))
            is_internal = request.form.get("is_internal") == "on"
            saved = 0
            invalid = 0
            for key, value in request.form.items():
                if not key.startswith("marks_"):
                    continue
                identifier = key[6:]
                marks = value.strip()
                student_user = db.session.get(User, int(identifier)) if identifier.isdigit() else User.query.filter_by(enrollment_no=identifier, role="Student").first()
                if not student_user or student_user.role != "Student" or not marks:
                    continue
                try:
                    if float(marks) > out_of_marks:
                        invalid += 1
                        continue
                except ValueError:
                    pass
                result = StudentResult.query.filter_by(student_user_id=student_user.id, subject=subject, exam=exam).first()
                if result is not None and result.teacher_user_id != user.id:
                    continue
                if result is None:
                    result = StudentResult(student_user_id=student_user.id, subject=subject, exam=exam)
                    db.session.add(result)
                result.teacher_user_id = user.id
                result.marks_grade = marks
                result.out_of_marks = out_of_marks
                result.is_internal = is_internal
                saved += 1
            db.session.commit()
            flash(f"Results saved for {saved} student(s).")
            if invalid:
                flash(f"{invalid} mark(s) exceeded the Out of Marks value and were skipped.")
            return redirect(url_for("manage_materials", result_subject=subject, result_exam=exam))
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
            create_material_notifications(material)
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
        nav_items=ROLE_NAV_ITEMS["Teacher"],
        active_endpoint="manage_materials",
        teacher_profile=teacher_profile,
        material_types=sorted(MATERIAL_TYPES),
        material_upload_rules=MATERIAL_UPLOAD_RULES,
        teacher_subjects=[teacher_profile.subject] if teacher_profile.subject else [],
        materials=materials,
        result_departments=result_departments,
        result_semesters=result_semesters,
        result_divisions=result_divisions,
        result_subjects=result_subjects,
        result_students=result_students,
        result_department=result_department,
        result_semester=result_semester,
        result_division=result_division,
        result_subject=result_subject,
        result_exam=result_exam,
        existing_results=existing_results,
        existing_out_of_marks=existing_out_of_marks,
        existing_is_internal=existing_is_internal,
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


@app.route("/teacher/lectures", methods=["GET", "POST"])
def teacher_lectures():
    user = get_current_user_for_role("Teacher")
    if not user:
        return redirect(url_for("login"))
    if request.method == "POST":
        action = request.form.get("action", "add")
        if action == "delete":
            lecture = WeeklySchedule.query.filter_by(id=request.form.get("lecture_id", type=int), student_user_id=user.id).first_or_404()
            db.session.delete(lecture)
            db.session.commit()
            flash("Lecture deleted successfully.")
            return redirect(url_for("teacher_lectures"))
        lecture = WeeklySchedule.query.filter_by(id=request.form.get("lecture_id", type=int), student_user_id=user.id).first() if action == "update" else None
        if lecture is None:
            lecture = WeeklySchedule(student_user_id=user.id, teacher=user.full_name)
            db.session.add(lecture)
        lecture.day_of_week = request.form.get("day_of_week", type=int)
        lecture.subject = request.form.get("subject", "").strip()
        lecture.department = request.form.get("department", "").strip() or None
        lecture.start_time = request.form.get("start_time", "").strip()
        lecture.end_time = request.form.get("end_time", "").strip()
        lecture.room = request.form.get("room", "").strip() or None
        assigned_subject_names = {
            assignment.subject.name
            for assignment in TeacherSubjectAssignment.query.filter_by(
                teacher_user_id=user.id
            ).join(Subject).all()
            if assignment.subject and assignment.subject.name
        }
        valid_schedule_departments = {department.name for department in Department.query.all()}
        if lecture.department not in valid_schedule_departments:
            flash("Select a department added by the administrator.")
            return redirect(url_for("teacher_lectures"))
        if lecture.subject not in assigned_subject_names:
            flash("Select a subject assigned to you.")
            return redirect(url_for("teacher_lectures"))
        if lecture.day_of_week is None or not lecture.subject or not lecture.start_time or not lecture.end_time:
            flash("Day, subject, start time, and end time are required.")
            return redirect(url_for("teacher_lectures"))
        db.session.commit()
        flash("Lecture saved successfully.")
        return redirect(url_for("teacher_lectures"))
    lectures = WeeklySchedule.query.filter_by(
        student_user_id=user.id, teacher=user.full_name,
    ).order_by(WeeklySchedule.day_of_week, WeeklySchedule.start_time).all()
    teacher_subjects = sorted({
        assignment.subject.name
        for assignment in TeacherSubjectAssignment.query.filter_by(
            teacher_user_id=user.id
        ).join(Subject).all()
        if assignment.subject and assignment.subject.name
    }, key=str.casefold)
    schedule_departments = [department.name for department in Department.query.order_by(Department.name).all()]
    return render_template("dashboard_section.html", current_user=user, role="Teacher", css_file="css/teacher.css", nav_items=ROLE_NAV_ITEMS["Teacher"], active_endpoint="teacher_lectures", section_title="Weekly Schedule", section_name="lectures", section_icon="fa-calendar-days", table_headers=[], table_rows=[], empty_message="No lectures scheduled yet.", schedules=lectures, teacher_subjects=teacher_subjects, schedule_departments=schedule_departments)


@app.route("/student/notifications/<int:notification_id>")
def open_student_notification(notification_id):
    user = get_current_user_for_role("Student")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    notification = StudentNotification.query.filter_by(
        id=notification_id, student_user_id=user.id
    ).first_or_404()
    notification.read_at = datetime.utcnow()
    db.session.commit()
    material = db.session.get(AcademicMaterial, notification.material_id)
    if material and material.stored_filename:
        return redirect(url_for("download_material", material_id=material.id))
    section = {
        "Assignment": "student_assignments", "Study Material": "student_materials",
        "Notice": "student_notices", "Academic Calendar": "student_calendar",
        "Attendance": "student_attendance", "Result": "student_results",
        "Timetable": "student_timetable",
    }.get(notification.material_type, "student_notices")
    return redirect(url_for(section))


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
    requested_student_id = request.args.get("student_id", type=int)
    selected_student = get_parent_connected_student(user, requested_student_id)
    if requested_student_id and not selected_student:
        flash("You can only view connected students.")
        return redirect(url_for("parent"))
    if not selected_student and connected_students:
        selected_student = connected_students[0]
    attendance_student_name = None
    recent_results = []
    upcoming_events = []
    performance_average = None
    overall_attendance = None
    today_attendance_by_student = []
    if selected_student:
        student_user = selected_student[0]
        student_profile = selected_student[1]
        attendance_student_name = student_user.full_name
        overall_attendance = get_attendance_summary(student_user.id)[1]
        today = datetime.today().date()
        for child_user, _child_profile in [selected_student]:
            records = Attendance.query.filter_by(
                student_user_id=child_user.id,
                date=today,
            ).order_by(Attendance.start_time.desc()).all()
            if records:
                present_count = sum(record.status == "Present" for record in records)
                total_count = len(records)
                status = "Present" if present_count > 0 else "Absent"
            else:
                present_count = 0
                total_count = 0
                status = "Not Marked"
            today_attendance_by_student.append({
                "name": child_user.full_name,
                "status": status,
                "present": present_count,
                "total": total_count,
                "date": today.strftime("%d %b %Y"),
            })
        for result in StudentResult.query.filter_by(
            student_user_id=student_user.id
        ).order_by(StudentResult.updated_at.desc()).limit(5).all():
            percentage = None
            try:
                if result.out_of_marks and float(result.out_of_marks) > 0:
                    percentage = round(
                        float(result.marks_grade) / float(result.out_of_marks) * 100, 2
                    )
            except (TypeError, ValueError):
                pass
            recent_results.append({
                "subject": result.subject,
                "exam": result.exam,
                "marks": result.marks_grade,
                "out_of_marks": result.out_of_marks,
                "percentage": percentage,
            })
        internal_percentages = []
        for result in StudentResult.query.filter_by(
            student_user_id=student_user.id, is_internal=True
        ).all():
            try:
                if result.out_of_marks and float(result.out_of_marks) > 0:
                    internal_percentages.append(
                        float(result.marks_grade) / float(result.out_of_marks) * 100
                    )
            except (TypeError, ValueError):
                continue
        if internal_percentages:
            performance_average = round(
                sum(internal_percentages) / len(internal_percentages), 2
            )
        upcoming_events = AcademicMaterial.query.filter(
            AcademicMaterial.department == student_profile.department,
            AcademicMaterial.material_type.in_(["Academic Calendar", "Notice"]),
        ).order_by(AcademicMaterial.uploaded_at.desc()).limit(5).all()

    return render_template(
        "parent.html",
        current_user=user,
        connected_students=connected_students,
        selected_student_id=selected_student[0].id if selected_student else None,
        parent_student_options=[{"id": child.id, "name": child.full_name, "enrollment": child.enrollment_no or ""} for child, _ in connected_students],
        attendance_student_name=attendance_student_name,
        today_attendance=today_attendance_by_student[0] if today_attendance_by_student else None,
        today_attendance_by_student=today_attendance_by_student,
        overall_attendance=overall_attendance,
        recent_results=recent_results,
        upcoming_events=upcoming_events,
        performance_average=performance_average,
    )


@app.route("/parent/profile")
def parent_profile():
    user = get_current_user_for_role("Parent")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    return render_template("parent_profile.html", current_user=user)


@app.route("/parent/profile/edit", methods=["GET", "POST"])
def edit_parent_profile():
    user = get_current_user_for_role("Parent")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        if not full_name or not email:
            flash("Full name and email are required.")
            return redirect(url_for("edit_parent_profile"))
        if User.query.filter(User.email == email, User.id != user.id).first():
            flash("Email already registered!")
            return redirect(url_for("edit_parent_profile"))
        user.full_name = full_name
        user.email = email
        user.phone = request.form.get("phone", "").strip() or None
        db.session.commit()
        flash("Profile updated successfully!")
        return redirect(url_for("parent_profile"))
    return render_template("edit_parent_profile.html", current_user=user)


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
    if material_type == "Notice":
        requested_student_id = None
    selected_student = get_parent_connected_student(user, requested_student_id)
    if requested_student_id and not selected_student:
        flash("You can only view data for a connected student.")
        return redirect(url_for("parent"))
    if not selected_student and connected_students:
        selected_student = connected_students[0]

    materials = []
    student_results = []
    notifications = []
    attendance_summary = []
    if selected_student:
        student_user, student_profile = selected_student
        if material_type == "Result":
            student_results = StudentResult.query.filter_by(
                student_user_id=student_user.id
            ).order_by(StudentResult.updated_at.desc()).all()
        elif material_type != "Notice":
            if material_type == "Attendance":
                attendance_summary = get_attendance_summary(student_user.id)[0]
            else:
                materials = AcademicMaterial.query.filter_by(
                    material_type=material_type,
                    department=student_profile.department,
                ).order_by(AcademicMaterial.uploaded_at.desc()).all()
    if material_type == "Notice":
        connected_ids = [student_user.id for student_user, _ in connected_students]
        if connected_ids:
            notifications = StudentNotification.query.filter(
                StudentNotification.student_user_id.in_(connected_ids)
            ).order_by(StudentNotification.created_at.desc()).all()

    return render_template(
        "parent_academic_section.html",
        current_user=user,
        connected_students=connected_students,
        selected_student=selected_student,
        materials=materials,
        student_results=student_results,
        notifications=notifications,
        attendance_summary=attendance_summary,
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
    return render_parent_academic_section(
        "Notice", "Notices", "fa-bell", "No notices available yet."
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
    departments = Department.query.count()
    recent_notices = AcademicMaterial.query.filter_by(
        material_type="Notice"
    ).order_by(AcademicMaterial.uploaded_at.desc()).limit(5).all()
    return render_template(
        "admin.html",
        current_user=user,
        students=students,
        teachers=teachers,
        parents=parents,
        departments=departments,
        recent_notices=recent_notices,
    )


@app.route("/admin/management", methods=["GET", "POST"])
def admin_management():
    current_admin = get_current_user_for_role("Admin")
    if not current_admin:
        flash("Access denied!")
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action", "create")
        if action == "delete":
            target = db.session.get(User, request.form.get("user_id", type=int))
            admin_count = User.query.filter_by(role="Admin").count()
            if not target or target.role != "Admin":
                flash("Admin not found.")
            elif target.id == current_admin.id:
                flash("You cannot delete your own admin account.")
            elif admin_count <= 1:
                flash("The last admin account cannot be deleted.")
            else:
                db.session.delete(target)
                db.session.commit()
                flash("Admin removed successfully.")
            return redirect(url_for("admin_management"))

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip() or None
        admin_id = request.form.get("admin_id", "").strip()
        password = request.form.get("password", "")
        if not full_name or not email or not admin_id or not password:
            flash("Full name, email, Admin ID, and password are required.")
        elif User.query.filter(func.lower(User.email) == email.casefold()).first():
            flash("Email already registered.")
        elif User.query.filter(func.lower(User.admin_id) == admin_id.casefold()).first():
            flash("Admin ID already exists.")
        else:
            new_admin = User(
                full_name=full_name,
                email=email,
                phone=phone,
                admin_id=admin_id,
                password=bcrypt.generate_password_hash(password).decode("utf-8"),
                role="Admin",
            )
            db.session.add(new_admin)
            db.session.commit()
            flash("Admin account created successfully.")
        return redirect(url_for("admin_management"))

    admins = User.query.filter_by(role="Admin").order_by(User.full_name.asc()).all()
    return render_template("admin_management.html", current_user=current_admin, admins=admins)


@app.route("/admin/profile")
def admin_profile():
    user = get_current_user_for_role("Admin")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    return render_template("admin_profile.html", current_user=user)


@app.route("/admin/profile/edit", methods=["GET", "POST"])
def edit_admin_profile():
    user = get_current_user_for_role("Admin")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        if not full_name or not email:
            flash("Full name and email are required.")
            return redirect(url_for("edit_admin_profile"))
        if User.query.filter(User.email == email, User.id != user.id).first():
            flash("Email already registered!")
            return redirect(url_for("edit_admin_profile"))
        user.full_name = full_name
        user.email = email
        user.phone = request.form.get("phone", "").strip() or None
        db.session.commit()
        flash("Profile updated successfully!")
        return redirect(url_for("admin_profile"))
    return render_template("edit_admin_profile.html", current_user=user)


def admin_user_rows(role, identifier_field, include_ids=False, search_query=""):
    users = User.query.filter_by(role=role).all()
    search_query = (search_query or "").strip().casefold()
    if search_query:
        users = [user for user in users if search_query in " ".join([
            user.full_name or "", user.email or "", getattr(user, identifier_field) or ""
        ]).casefold()]
    rows = [
        [
            user.full_name,
            getattr(user, identifier_field) or "Not available",
            user.email or "Not available",
            user.phone or "Not available",
        ]
        for user in users
    ]
    return (rows, [user.id for user in users]) if include_ids else rows


def delete_admin_user(user, target_role):
    if not user or user.role != target_role:
        return False, "User not found."
    if target_role == "Student":
        ParentStudentConnection.query.filter(
            (ParentStudentConnection.student_user_id == user.id) |
            (ParentStudentConnection.parent_user_id == user.id)
        ).delete(synchronize_session=False)
        Student.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        StudentResult.query.filter_by(student_user_id=user.id).delete(synchronize_session=False)
        StudentNotification.query.filter_by(student_user_id=user.id).delete(synchronize_session=False)
        WeeklySchedule.query.filter_by(student_user_id=user.id).delete(synchronize_session=False)
        StudentFinalResult.query.filter_by(student_user_id=user.id).delete(synchronize_session=False)
    elif target_role == "Teacher":
        Teacher.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        TeacherSubjectAssignment.query.filter_by(teacher_user_id=user.id).delete(synchronize_session=False)
        StudentResult.query.filter_by(teacher_user_id=user.id).delete(synchronize_session=False)
        material_ids = [m.id for m in AcademicMaterial.query.filter_by(teacher_user_id=user.id).all()]
        if material_ids:
            StudentNotification.query.filter(StudentNotification.material_id.in_(material_ids)).delete(synchronize_session=False)
        AcademicMaterial.query.filter_by(teacher_user_id=user.id).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()
    return True, f"{target_role} removed successfully."


@app.route("/admin/students", methods=["GET", "POST"])
def admin_students():
    user = get_current_user_for_role("Admin")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    if request.method == "POST":
        target = db.session.get(User, request.form.get("user_id", type=int))
        if target and target.id != user.id:
            _, message = delete_admin_user(target, "Student")
            flash(message)
        else:
            flash("Student not found.")
        return redirect(url_for("admin_students"))
    search_query = request.args.get("q", "")
    rows, ids = admin_user_rows("Student", "enrollment_no", True, search_query)
    return render_role_section("Admin", "students", rows, ids, search_query)


@app.route("/admin/teachers", methods=["GET", "POST"])
def admin_teachers():
    user = get_current_user_for_role("Admin")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    if request.method == "POST":
        target = db.session.get(User, request.form.get("user_id", type=int))
        if target and target.id != user.id:
            _, message = delete_admin_user(target, "Teacher")
            flash(message)
        else:
            flash("Teacher not found.")
        return redirect(url_for("admin_teachers"))
    search_query = request.args.get("q", "")
    rows, ids = admin_user_rows("Teacher", "employee_id", True, search_query)
    return render_role_section("Admin", "teachers", rows, ids, search_query)


@app.route("/admin/parents", methods=["GET", "POST"])
def admin_parents():
    user = get_current_user_for_role("Admin")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))
    if request.method == "POST":
        target = db.session.get(User, request.form.get("user_id", type=int))
        if target and target.id != user.id:
            ParentStudentConnection.query.filter(
                (ParentStudentConnection.parent_user_id == target.id) |
                (ParentStudentConnection.student_user_id == target.id)
            ).delete(synchronize_session=False)
            db.session.delete(target)
            db.session.commit()
            flash("Parent removed successfully.")
        else:
            flash("Parent not found.")
        return redirect(url_for("admin_parents"))
    search_query = request.args.get("q", "")
    rows, ids = admin_user_rows("Parent", "parent_id", True, search_query)
    return render_role_section("Admin", "parents", rows, ids, search_query)


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


@app.route("/admin/subject-assignments", methods=["GET", "POST"])
def admin_subject_assignments():
    user = get_current_user_for_role("Admin")
    if not user:
        flash("Access denied!")
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action", "add")
        assignment_id = request.form.get("assignment_id", type=int)
        department = request.form.get("department", "").strip()
        subject_name = request.form.get("subject_name", "").strip()
        division = request.form.get("division", "").strip().upper()
        teacher_id = request.form.get("teacher_id", type=int)
        semester = request.form.get("semester", type=int)

        if action == "delete":
            assignment = db.session.get(TeacherSubjectAssignment, assignment_id)
            if assignment:
                db.session.delete(assignment)
                db.session.commit()
                flash("Subject assignment deleted.")
            else:
                flash("Subject assignment not found.")
            return redirect(url_for("admin_subject_assignments"))

        teacher = User.query.filter_by(id=teacher_id, role="Teacher").first()
        department_record = Department.query.filter_by(name=department).first()
        if not department_record or not subject_name or semester not in range(1, 9) or division not in {"A", "B", "C"} or not teacher:
            flash("Select a valid department, semester, division, subject, and teacher.")
            return redirect(url_for("admin_subject_assignments"))

        subject = Subject.query.filter(
            func.lower(Subject.name) == subject_name.casefold(),
            func.lower(Subject.department) == department.casefold(),
        ).first()
        if not subject:
            subject = Subject(department=department, name=subject_name)
            db.session.add(subject)
            db.session.flush()

        duplicate_query = TeacherSubjectAssignment.query.filter_by(
            teacher_user_id=teacher.id,
            subject_id=subject.id,
            semester=semester,
            division=division,
        )
        if assignment_id:
            duplicate_query = duplicate_query.filter(TeacherSubjectAssignment.id != assignment_id)
        if duplicate_query.first():
            flash("That subject assignment already exists.")
            return redirect(url_for("admin_subject_assignments"))

        assignment = db.session.get(TeacherSubjectAssignment, assignment_id) if assignment_id else None
        if not assignment:
            assignment = TeacherSubjectAssignment()
            db.session.add(assignment)
        assignment.teacher_user_id = teacher.id
        assignment.subject_id = subject.id
        assignment.semester = semester
        assignment.division = division
        db.session.commit()
        flash("Subject assignment saved successfully.")
        return redirect(url_for("admin_subject_assignments"))

    assignments = TeacherSubjectAssignment.query.join(Subject).join(User, User.id == TeacherSubjectAssignment.teacher_user_id).order_by(Subject.department, Subject.name, TeacherSubjectAssignment.semester, TeacherSubjectAssignment.division).all()
    return render_template(
        "admin_subject_assignments.html",
        current_user=user,
        assignments=assignments,
        departments=get_departments(),
        teachers=User.query.filter_by(role="Teacher").order_by(User.full_name).all(),
        semesters=range(1, 9),
        divisions=("A", "B", "C"),
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    logout_user()
    session.clear()

    flash(
        "You have been logged out."
    )

    response = redirect(url_for("login"))
    # Flask-Login normally schedules this deletion through its response hook.
    # Delete it explicitly as well so the remember token cannot restore this
    # account after a manual logout, regardless of cookie configuration.
    response.delete_cookie(
        app.config.get("REMEMBER_COOKIE_NAME", "remember_token"),
        path=app.config.get("REMEMBER_COOKIE_PATH", "/"),
        domain=app.config.get("REMEMBER_COOKIE_DOMAIN"),
    )
    return response


# ==========================================
# CREATE DATABASE
# ==========================================

with app.app_context():

    db.create_all()
    ensure_user_identifier_columns()
    ensure_student_profile_columns()
    ensure_teacher_profile_columns()
    ensure_academic_material_columns()
    ensure_weekly_schedule_columns()
    ensure_student_result_columns()
    ensure_teacher_subject_assignment_columns()
    seed_departments()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
