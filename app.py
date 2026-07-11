from flask import Flask, render_template, request, redirect
from config import Config
from models import db
from models.user import User
from models.student import Student
from models.teacher import Teacher

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)


# -----------------------
# Routes
# -----------------------

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        print("Email:", email)
        print("Password:", password)

        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        print(user)

        if user:

            if user.role == "admin":
                return redirect('/admin')

            elif user.role == "teacher":
                return redirect('/teacher')

            elif user.role == "student":
                return redirect('/student')

            elif user.role == "parent":
                return redirect('/parent')

        return "Invalid Login"

    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/student")
def student():
    return render_template("student.html")


@app.route("/teacher")
def teacher():
    return render_template("teacher.html")


@app.route("/parent")
def parent():
    return render_template("parent.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


# -----------------------
# Create Database
# -----------------------

with app.app_context():

    db.create_all()


if __name__ == "__main__":

    app.run(debug=True)
