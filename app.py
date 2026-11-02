import os

from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL, select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "teamforge-development-secret")

db_password = os.getenv("DB_PASSWORD")

if not db_password:
    raise RuntimeError(
        "DB_PASSWORD is missing. Check your .env file."
    )

app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER", "root"),
    password=db_password,
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "teamforge"),
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# These models map to the tables already present in the TeamForge database.
# Do not call db.create_all() during this migration; it is not needed for
# existing tables and we do not want to recreate or overwrite your database.
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    department = db.Column(db.String(100))
    semester = db.Column(db.Integer)
    interests = db.Column(db.Text)
    availability = db.Column(db.String(100))


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(100))


class UserSkill(db.Model):
    __tablename__ = "user_skills"

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True, nullable=False
    )
    skill_id = db.Column(
        db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True, nullable=False
    )
    proficiency = db.Column(db.Integer, nullable=False)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creator_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    team_size = db.Column(db.Integer, nullable=False)
    project_type = db.Column(db.String(100))
    created_at = db.Column(
        db.DateTime, server_default=db.func.current_timestamp()
    )


class ProjectRequirement(db.Model):
    __tablename__ = "project_requirements"

    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True, nullable=False
    )
    skill_id = db.Column(
        db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True, nullable=False
    )
    importance = db.Column(db.Integer, default=3)


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    created_at = db.Column(
        db.DateTime, server_default=db.func.current_timestamp()
    )


class TeamMember(db.Model):
    __tablename__ = "team_members"

    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True, nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True, nullable=False
    )


class TeamRequest(db.Model):
    __tablename__ = "team_requests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False
    )
    sender_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    receiver_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(
        db.DateTime, server_default=db.func.current_timestamp()
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match", 400
        if not name or not email or not password:
            return "Please complete all required fields.", 400

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return "Registration failed: this email may already be registered.", 409
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception("Registration failed")
            return "Registration failed. Please try again.", 500

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/students")
def students():
    students_list = db.session.execute(
        select(User.id, User.name, User.email).order_by(User.name)
    ).mappings().all()
    return render_template("students.html", students=students_list)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = db.session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("profile"))

        return "Invalid email or password.", 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = db.session.execute(
        select(User.id, User.name, User.email).where(User.id == user_id)
    ).mappings().first()

    profile_data = db.session.execute(
        select(
            Profile.department, Profile.semester,
            Profile.interests, Profile.availability
        ).where(Profile.user_id == user_id)
    ).mappings().first()

    skills_list = db.session.execute(
        select(
            Skill.id, Skill.name, UserSkill.proficiency
        )
        .join(UserSkill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == user_id)
        .order_by(Skill.name)
    ).mappings().all()

    return render_template(
        "profile.html", user=user, profile=profile_data, skills=skills_list
    )


@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        department = request.form["department"].strip()
        try:
            semester = int(request.form["semester"])
        except (TypeError, ValueError):
            return "Invalid semester.", 400
        interests = request.form["interests"].strip()
        availability = request.form["availability"]

        if semester < 1 or semester > 8:
            return "Semester must be between 1 and 8.", 400

        profile_record = db.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        ).scalar_one_or_none()

        if profile_record:
            profile_record.department = department
            profile_record.semester = semester
            profile_record.interests = interests
            profile_record.availability = availability
        else:
            db.session.add(Profile(
                user_id=user_id,
                department=department,
                semester=semester,
                interests=interests,
                availability=availability,
            ))

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception("Profile update failed")
            return "Could not save your profile. Please try again.", 500

        return redirect(url_for("profile"))

    profile_data = db.session.execute(
        select(
            Profile.department, Profile.semester,
            Profile.interests, Profile.availability
        ).where(Profile.user_id == user_id)
    ).mappings().first()

    return render_template("edit_profile.html", profile=profile_data)


@app.route("/skills")
def skills():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    all_skills = db.session.execute(
        select(Skill.id, Skill.name).order_by(Skill.name)
    ).mappings().all()

    user_skills = db.session.execute(
        select(Skill.id, Skill.name, UserSkill.proficiency)
        .join(UserSkill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == user_id)
        .order_by(Skill.name)
    ).mappings().all()

    return render_template(
        "skills.html", all_skills=all_skills, user_skills=user_skills
    )


@app.route("/skills/add", methods=["POST"])
def add_skill():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    try:
        skill_id = int(request.form["skill_id"])
        proficiency = int(request.form["proficiency"])
    except (KeyError, TypeError, ValueError):
        return "Invalid skill or proficiency.", 400

    if not 1 <= proficiency <= 5:
        return "Invalid proficiency. Choose a value from 1 to 5.", 400
    if db.session.get(Skill, skill_id) is None:
        return "Skill not found.", 404

    user_skill = db.session.get(UserSkill, (user_id, skill_id))
    if user_skill:
        user_skill.proficiency = proficiency
    else:
        db.session.add(UserSkill(
            user_id=user_id, skill_id=skill_id, proficiency=proficiency
        ))

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Could not save skill")
        return "Could not save skill. Please try again.", 500

    return redirect(url_for("skills"))


@app.route("/skills/remove/<int:skill_id>", methods=["POST", "GET"])
def remove_skill(skill_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user_skill = db.session.get(UserSkill, (user_id, skill_id))
    if user_skill:
        db.session.delete(user_skill)
        db.session.commit()

    return redirect(url_for("skills"))


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = db.session.execute(
        select(User.id, User.name, User.email).where(User.id == user_id)
    ).mappings().first()

    profile_data = db.session.execute(
        select(
            Profile.department, Profile.semester,
            Profile.interests, Profile.availability
        ).where(Profile.user_id == user_id)
    ).mappings().first()

    skills_list = db.session.execute(
        select(Skill.name, UserSkill.proficiency)
        .join(UserSkill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == user_id)
        .order_by(Skill.name)
    ).mappings().all()

    completion = 0
    if user:
        completion += 25
    if profile_data:
        if profile_data["department"]:
            completion += 15
        if profile_data["semester"]:
            completion += 15
        if profile_data["availability"]:
            completion += 15
    if skills_list:
        completion += 30

    return render_template(
        "dashboard.html",
        user=user,
        profile=profile_data,
        skills=skills_list,
        completion=completion,
    )


@app.route("/project/create", methods=["GET", "POST"])
def create_project():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        description = request.form["description"].strip()
        project_type = request.form["project_type"]
        try:
            team_size = int(request.form["team_size"])
        except (TypeError, ValueError):
            return "Invalid team size.", 400

        if not name:
            return "Project name is required.", 400
        if not 2 <= team_size <= 8:
            return "Team size must be between 2 and 8.", 400

        project = Project(
            creator_id=user_id,
            name=name,
            description=description,
            team_size=team_size,
            project_type=project_type,
        )
        db.session.add(project)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception("Project creation failed")
            return "Could not create project. Please try again.", 500

        return redirect(url_for("my_projects"))

    return render_template("create_project.html")


@app.route("/projects")
def my_projects():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    projects_list = db.session.execute(
        select(
            Project.id, Project.name, Project.description,
            Project.team_size, Project.project_type, Project.created_at
        )
        .where(Project.creator_id == user_id)
        .order_by(Project.created_at.desc())
    ).mappings().all()

    return render_template("projects.html", projects=projects_list)


@app.route("/project/<int:project_id>/requirements", methods=["GET", "POST"])
def project_requirements(project_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    project = db.session.execute(
        select(
            Project.id, Project.name, Project.description,
            Project.team_size, Project.project_type
        ).where(
            Project.id == project_id,
            Project.creator_id == user_id,
        )
    ).mappings().first()

    if not project:
        return "Project not found or access denied.", 404

    all_skills = db.session.execute(
        select(Skill.id, Skill.name, Skill.category).order_by(Skill.name)
    ).mappings().all()

    if request.method == "POST":
        new_requirements = []
        for skill in all_skills:
            skill_id = skill["id"]
            if request.form.get(f"skill_{skill_id}"):
                try:
                    importance = int(request.form.get(f"importance_{skill_id}", 3))
                except (TypeError, ValueError):
                    return "Invalid importance value.", 400
                if not 1 <= importance <= 5:
                    return "Importance must be between 1 and 5.", 400
                new_requirements.append(ProjectRequirement(
                    project_id=project_id,
                    skill_id=skill_id,
                    importance=importance,
                ))

        try:
            db.session.execute(
                delete(ProjectRequirement).where(
                    ProjectRequirement.project_id == project_id
                )
            )
            db.session.add_all(new_requirements)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception("Saving project requirements failed")
            return "Could not save requirements. Please try again.", 500

        return redirect(url_for("project_requirements", project_id=project_id))

    requirements = db.session.execute(
        select(
            ProjectRequirement.skill_id,
            ProjectRequirement.importance,
            Skill.name,
        )
        .join(Skill, ProjectRequirement.skill_id == Skill.id)
        .where(ProjectRequirement.project_id == project_id)
        .order_by(Skill.name)
    ).mappings().all()

    return render_template(
        "project_requirements.html",
        project=project,
        all_skills=all_skills,
        requirements=requirements,
    )


@app.route("/project/<int:project_id>/match")
def match_project(project_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    # Only the project's creator can view its recommendations.
    project = db.session.execute(
        select(Project).where(
            Project.id == project_id,
            Project.creator_id == user_id
        )
    ).scalar_one_or_none()

    if not project:
        return "Project not found or access denied.", 404

    # Fetch the project's required skills.
    requirement_rows = db.session.execute(
        select(
            ProjectRequirement.skill_id,
            ProjectRequirement.importance,
            Skill.name
        )
        .join(Skill, Skill.id == ProjectRequirement.skill_id)
        .where(ProjectRequirement.project_id == project_id)
        .order_by(Skill.name)
    ).mappings().all()

    requirements = [
        {
            "skill_id": row["skill_id"],
            "name": row["name"],
            "importance": row["importance"] or 3
        }
        for row in requirement_rows
    ]

    # Fetch potential teammates and their availability.
    candidate_rows = db.session.execute(
        select(User.id, User.name, Profile.availability)
        .outerjoin(Profile, Profile.user_id == User.id)
        .where(User.id != user_id)
        .order_by(User.name)
    ).mappings().all()

    # Fetch candidates' skills and proficiency levels.
    skill_rows = db.session.execute(
        select(
            UserSkill.user_id,
            Skill.id.label("skill_id"),
            Skill.name,
            UserSkill.proficiency
        )
        .join(Skill, Skill.id == UserSkill.skill_id)
    ).mappings().all()

    skills_by_user = {}
    for row in skill_rows:
        skills_by_user.setdefault(row["user_id"], {})[
            row["skill_id"]
        ] = {
            "name": row["name"],
            "proficiency": row["proficiency"]
        }

    total_importance = sum(
        requirement["importance"] for requirement in requirements
    )

    candidates = []

    for candidate in candidate_rows:
        candidate_skills = skills_by_user.get(candidate["id"], {})

        matched_skills = []
        missing_skills = []
        proficiency_values = []
        covered_importance = 0

        for requirement in requirements:
            skill = candidate_skills.get(requirement["skill_id"])

            if skill:
                matched_skills.append(skill["name"])
                proficiency_values.append(skill["proficiency"])
                covered_importance += requirement["importance"]
            else:
                missing_skills.append(requirement["name"])

        match_score = (
            round(covered_importance / total_importance * 100)
            if total_importance else 0
        )

        average_proficiency = (
            round(sum(proficiency_values) / len(proficiency_values), 1)
            if proficiency_values else 0
        )

        candidates.append({
            "id": candidate["id"],
            "name": candidate["name"],
            "availability": candidate["availability"] or "Not specified",
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_score": match_score,
            "average_proficiency": average_proficiency
        })

    # Remove candidates who have no matching required skills.
    candidates = [
        candidate for candidate in candidates
        if candidate["match_score"] > 0
    ]

    candidates.sort(
        key=lambda candidate: (
            candidate["match_score"],
            candidate["average_proficiency"]
        ),
        reverse=True
    )

    return render_template(
        "match_project.html",
        project=project,
        requirements=requirements,
        candidates=candidates
    )


@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
