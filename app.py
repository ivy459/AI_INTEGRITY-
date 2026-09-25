from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.security import check_password_hash

app = Flask(__name__)

app.secret_key = "ai-exam-integrity-development-key"


# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "database",
    "exam_integrity.db"
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    if not username or not password or not role:
        return render_template(
            "login.html",
            error="Please complete all login fields."
        )

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    connection.close()

    if user is None:
        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    if not check_password_hash(user["password"], password):
        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    if user["role"] != role:
        return render_template(
            "login.html",
            error="The selected role does not match this account."
        )

    # Create login session
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    # Redirect according to role
    if user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    if user["role"] == "invigilator":
        return redirect(url_for("invigilator_dashboard"))

    return redirect(url_for("home"))


# ============================================================
# ADMIN ACCESS PROTECTION
# ============================================================

def admin_required():

    if "user_id" not in session:
        return False

    if session.get("role") != "admin":
        return False

    return True


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin_dashboard():

    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    # Total students
    total_students = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM students
        """
    ).fetchone()["total"]

    # Active examinations
    active_examinations = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM examinations
        WHERE status = 'ongoing'
        """
    ).fetchone()["total"]

    # Total invigilators
    total_invigilators = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM invigilators
        """
    ).fetchone()["total"]

    # Open incidents
    open_incidents = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM incidents
        WHERE status = 'open'
        """
    ).fetchone()["total"]

    # Examinations
    examinations = connection.execute(
        """
        SELECT *
        FROM examinations
        ORDER BY examination_date, start_time
        """
    ).fetchall()

    # Recent incidents
    incidents = connection.execute(
        """
        SELECT
            incidents.*,
            students.student_number,
            students.first_name,
            students.last_name,
            examinations.course_code

        FROM incidents

        LEFT JOIN students
            ON incidents.student_id = students.id

        LEFT JOIN examinations
            ON incidents.examination_id = examinations.id

        ORDER BY incidents.reported_at DESC

        LIMIT 5
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",

        total_students=total_students,

        active_examinations=active_examinations,

        total_invigilators=total_invigilators,

        open_incidents=open_incidents,

        examinations=examinations,

        incidents=incidents
    )


# ============================================================
# STUDENT MANAGEMENT
# ============================================================

@app.route("/admin/students")
def admin_students():

    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    students = connection.execute(
        """
        SELECT *
        FROM students
        ORDER BY id ASC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "students.html",
        students=students
    )


# ============================================================
# EXAMINATION MANAGEMENT
# ============================================================

@app.route("/admin/examinations")
def admin_examinations():

    if not admin_required():
        return redirect(url_for("login"))

    return render_template(
        "module_placeholder.html",

        page_title="Examination Management",

        page_icon="📝",

        page_description="Create, schedule and manage examinations."
    )


# ============================================================
# INVIGILATOR MANAGEMENT
# ============================================================

@app.route("/admin/invigilators")
def admin_invigilators():

    if not admin_required():
        return redirect(url_for("login"))

    return render_template(
        "module_placeholder.html",

        page_title="Invigilator Management",

        page_icon="👨‍🏫",

        page_description="Manage invigilators and examination assignments."
    )


# ============================================================
# INCIDENT MANAGEMENT
# ============================================================

@app.route("/admin/incidents")
def admin_incidents():

    if not admin_required():
        return redirect(url_for("login"))

    return render_template(
        "module_placeholder.html",

        page_title="Incident Management",

        page_icon="🚨",

        page_description="Review and manage examination integrity incidents."
    )


# ============================================================
# REPORTS
# ============================================================

@app.route("/admin/reports")
def admin_reports():

    if not admin_required():
        return redirect(url_for("login"))

    return render_template(
        "module_placeholder.html",

        page_title="Reports & Analytics",

        page_icon="📊",

        page_description="View examination reports, statistics and analytics."
    )


# ============================================================
# AI ANALYSIS
# ============================================================

@app.route("/admin/ai-analysis")
def admin_ai_analysis():

    if not admin_required():
        return redirect(url_for("login"))

    return render_template(
        "module_placeholder.html",

        page_title="AI Analysis",

        page_icon="🤖",

        page_description="Monitor AI-powered examination integrity analysis."
    )


# ============================================================
# SETTINGS
# ============================================================

@app.route("/admin/settings")
def admin_settings():

    if not admin_required():
        return redirect(url_for("login"))

    return render_template(
        "module_placeholder.html",

        page_title="System Settings",

        page_icon="⚙️",

        page_description="Configure system preferences and administrator settings."
    )


# ============================================================
# INVIGILATOR DASHBOARD
# ============================================================

@app.route("/invigilator")
def invigilator_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "invigilator":
        return redirect(url_for("home"))

    return """
        <h1>Invigilator Dashboard</h1>

        <p>
            Invigilator dashboard coming soon.
        </p>

        <a href="/logout">
            Logout
        </a>
    """


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(debug=True)