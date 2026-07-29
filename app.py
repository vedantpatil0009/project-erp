from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db
from models.user import User 
from models.student import Student
from models.teacher import Teacher

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":
        print("Register button clicked!")
        email = request.form.get('email')
        password = request.form.get('password')

        print("Email:", email)
        print("Password:", password)

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):

        if user.role == "Student":
            return redirect(url_for("student"))

        elif user.role == "Teacher":
            return redirect(url_for("teacher"))

        elif user.role == "Parent":
            return redirect(url_for("parent"))

        elif user.role == "Admin":
            return redirect(url_for("admin"))

    flash("Invalid email or password")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        print("Name:", full_name)
        print("Email:", email)
        print("Password:", password)
        print("Role:", role)

        existing_user = User.query.filter_by(email=email).first()

        print("Existing User:", existing_user)

        if existing_user:
            flash("Email already registered!")
            print("Email already exists!")
            return redirect(url_for("register"))

        print("Form Data:", request.form)
        print("Password:", request.form.get("password"))
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")


        flash("Registration Successful!")
        return redirect(url_for("login"))

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




with app.app_context():

    db.create_all()


if __name__ == "__main__":

    app.run(debug=True)
