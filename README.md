# TeamForge

**A Student Project Collaboration and Team Matching Platform**

TeamForge is a web-based platform designed to help students find suitable teammates for academic projects and hackathons based on their technical skills and proficiency levels.

## Features

- User registration and authentication
- Student profiles with university information
- Technical skill management
- Project creation and management
- Project skill requirements
- Skill-based teammate matching
- Team invitations with accept and decline options
- Team management and member tracking
- Admin-managed hackathon catalogue
- Hackathon association with student projects

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL
- **ORM:** SQLAlchemy
- **Frontend:** HTML, CSS
- **Templating:** Jinja2

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Aditi-2008-tech/TeamForge.git
cd TeamForge
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

Windows:
```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file containing your local database configuration and Flask secret key.

Do not commit this file.

### 5. Set up the database

Create your MySQL database and execute the required SQL migration files.

### 6. Run the application

```bash
python app.py
```

Open the local address displayed in your terminal.

## Project Status

Semester project version: Initial working release.

Future improvements may include additional collaboration and project-management features.

## Author

Developed as an academic project.
