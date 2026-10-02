from flask import Flask, render_template, request, session, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
app = Flask(__name__)

app.secret_key = os.getenv( "SECRET_KEY", "teamforge-development-secret")

def get_db_connection():
    return mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "bae,bemywaifu",
    database = "teamforge",
    use_pure=True
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match"

        password_hash = generate_password_hash(password)

        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users(name, email,password_hash) VALUES(%s, %s, %s)", (name, email,password_hash))

            db.commit()

        except Exception as e:
            db.rollback()
            cursor.close()
            db.close()
            return f"Registeration failed: {e}"
        
        cursor.close()
        db.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/students")
def students():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email FROM users")
    students = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template(
        "students.html", students=students
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip(). lower()
        password = request.form["password"]
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = %s", (email,)
        )

        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("profile"))

        return "Invalid email or password."

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return "Please log in first."

    return f"Welcome, {session['user_name']}!"

@app.route("/profile")
def profile():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute ("""SELECT id, name, email FROM users WHERE id = %s""", (user_id,))

    user = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template("profile.html", user=user)

@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        department = request.form["department"].strip() 
        semester = int(request.form["semester"])
        interests = request.form["interests"].strip()
        availability = request.form["availability"]

        cursor.execute("""SELECT id FROM profiles WHERE user_id = %s""", (user_id,))

        existing_profile = cursor.fetchone()
        if existing_profile:
            cursor.execute("""UPDATE profiles SET department = %s, semester = %s, interests = %s, availability = %s WHERE user_id = %s""",(department, semester, interests, availability, user_id))

        else:
            cursor.execute("""INSERT INTO profiles(user_id, department, semester, interests, availability) VALUES (%s, %s, %s, %s, %s)""", (user_id, department, semester, interests, availability))

        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("profile"))

    cursor.execute("""SELECT department, semester, interests, availability FROM profiles WHERE user_id = %s""", (user_id,))

    profile = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template("edit_profile.html", profile=profile)

@app.route("/skills")
def skills():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, name
        FROM skills
        ORDER BY name
        """
    )

    all_skills = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            skills.id,
            skills.name,
            user_skills.proficiency
        FROM user_skills
        JOIN skills
            ON user_skills.skill_id = skills.id
        WHERE user_skills.user_id = %s
        ORDER BY skills.name
        """,
        (user_id,)
    )

    user_skills = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "skills.html",
        all_skills=all_skills,
        user_skills=user_skills
    )

@app.route("/skills/add", methods=["POST"])
def add_skill():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    skill_id = int(request.form["skill_id"])
    proficiency = int(request.form["proficiency"])

    if proficiency < 1 or proficiency > 5:
        return "Invalid proficiency."

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO user_skills
            (user_id, skill_id, proficiency)
            VALUES (%s, %s, %s)
            """,
            (user_id, skill_id, proficiency)
        )

        db.commit()

    except Exception:
        db.rollback()

    cursor.close()
    db.close()

    return redirect(url_for("skills"))

@app.route("/skills/remove/<int:skill_id>")
def remove_skill(skill_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM user_skills
        WHERE user_id = %s
        AND skill_id = %s
        """,
        (user_id, skill_id)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("skills"))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)