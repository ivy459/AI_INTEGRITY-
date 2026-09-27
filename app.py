from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "ai-exam-integrity-development-key"

DATABASE = os.path.join(os.path.dirname(__file__), "database", "exam_integrity.db")


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ============================================================
# ACCESS CONTROL HELPERS
# ============================================================

def admin_required():
    return "user_id" in session and session.get("role") == "admin"


def invigilator_required():
    return "user_id" in session and session.get("role") == "invigilator"


# ============================================================
# HOME / LOGIN / LOGOUT
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    if not username or not password or not role:
        return render_template("login.html", error="Please complete all login fields.")

    connection = get_db_connection()
    user = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    connection.close()

    if user is None or not check_password_hash(user["password"], password):
        return render_template("login.html", error="Invalid username or password.")

    if user["role"] != role:
        return render_template("login.html", error="The selected role does not match this account.")

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    if user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("invigilator_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    total_students = connection.execute("SELECT COUNT(*) AS total FROM students").fetchone()["total"]
    active_examinations = connection.execute(
        "SELECT COUNT(*) AS total FROM examinations WHERE status = 'ongoing'"
    ).fetchone()["total"]
    total_invigilators = connection.execute("SELECT COUNT(*) AS total FROM invigilators").fetchone()["total"]
    open_incidents = connection.execute(
        "SELECT COUNT(*) AS total FROM incidents WHERE status = 'open'"
    ).fetchone()["total"]

    examinations = connection.execute(
        "SELECT * FROM examinations ORDER BY examination_date, start_time"
    ).fetchall()

    incidents = connection.execute("""
        SELECT incidents.*, students.student_number, students.first_name, students.last_name,
               examinations.course_code
        FROM incidents
        LEFT JOIN students ON incidents.student_id = students.id
        LEFT JOIN examinations ON incidents.examination_id = examinations.id
        ORDER BY incidents.reported_at DESC
        LIMIT 5
    """).fetchall()

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
# STUDENT MANAGEMENT (full CRUD)
# ============================================================

@app.route("/admin/students")
def admin_students():
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    students = connection.execute("SELECT * FROM students ORDER BY id ASC").fetchall()
    connection.close()

    return render_template("students.html", students=students)


@app.route("/admin/students/add", methods=["GET", "POST"])
def add_student():
    if not admin_required():
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("student_form.html", student=None)

    student_number = request.form.get("student_number")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    course = request.form.get("course")
    year_of_study = request.form.get("year_of_study")

    if not student_number or not first_name or not last_name:
        return render_template(
            "student_form.html", student=None,
            error="Student number, first name and last name are required."
        )

    connection = get_db_connection()
    connection.execute("""
        INSERT INTO students (student_number, first_name, last_name, course, year_of_study)
        VALUES (?, ?, ?, ?, ?)
    """, (student_number, first_name, last_name, course, year_of_study))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_students"))


@app.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "GET":
        student = connection.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        connection.close()
        if student is None:
            return redirect(url_for("admin_students"))
        return render_template("student_form.html", student=student)

    student_number = request.form.get("student_number")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    course = request.form.get("course")
    year_of_study = request.form.get("year_of_study")

    connection.execute("""
        UPDATE students
        SET student_number = ?, first_name = ?, last_name = ?, course = ?, year_of_study = ?
        WHERE id = ?
    """, (student_number, first_name, last_name, course, year_of_study, student_id))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_students"))


@app.route("/admin/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_students"))


# ============================================================
# EXAMINATION MANAGEMENT (full CRUD)
# ============================================================

@app.route("/admin/examinations")
def admin_examinations():
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    examinations = connection.execute("""
        SELECT examinations.*, invigilators.first_name AS inv_first, invigilators.last_name AS inv_last
        FROM examinations
        LEFT JOIN invigilators ON examinations.invigilator_id = invigilators.id
        ORDER BY examination_date, start_time
    """).fetchall()
    connection.close()

    return render_template("examinations.html", examinations=examinations)


@app.route("/admin/examinations/add", methods=["GET", "POST"])
def add_examination():
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "GET":
        invigilators = connection.execute("SELECT * FROM invigilators ORDER BY first_name").fetchall()
        connection.close()
        return render_template("examination_form.html", examination=None, invigilators=invigilators)

    course_code = request.form.get("course_code")
    examination_name = request.form.get("examination_name")
    examination_date = request.form.get("examination_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    venue = request.form.get("venue")
    invigilator_id = request.form.get("invigilator_id") or None
    status = request.form.get("status")

    connection.execute("""
        INSERT INTO examinations
            (course_code, examination_name, examination_date, start_time, end_time, venue, invigilator_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (course_code, examination_name, examination_date, start_time, end_time, venue, invigilator_id, status))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_examinations"))


@app.route("/admin/examinations/edit/<int:examination_id>", methods=["GET", "POST"])
def edit_examination(examination_id):
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "GET":
        examination = connection.execute(
            "SELECT * FROM examinations WHERE id = ?", (examination_id,)
        ).fetchone()
        invigilators = connection.execute("SELECT * FROM invigilators ORDER BY first_name").fetchall()
        connection.close()
        if examination is None:
            return redirect(url_for("admin_examinations"))
        return render_template("examination_form.html", examination=examination, invigilators=invigilators)

    course_code = request.form.get("course_code")
    examination_name = request.form.get("examination_name")
    examination_date = request.form.get("examination_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    venue = request.form.get("venue")
    invigilator_id = request.form.get("invigilator_id") or None
    status = request.form.get("status")

    connection.execute("""
        UPDATE examinations
        SET course_code = ?, examination_name = ?, examination_date = ?, start_time = ?,
            end_time = ?, venue = ?, invigilator_id = ?, status = ?
        WHERE id = ?
    """, (course_code, examination_name, examination_date, start_time, end_time,
          venue, invigilator_id, status, examination_id))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_examinations"))


@app.route("/admin/examinations/delete/<int:examination_id>", methods=["POST"])
def delete_examination(examination_id):
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    connection.execute("DELETE FROM examinations WHERE id = ?", (examination_id,))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_examinations"))


# ============================================================
# INVIGILATOR MANAGEMENT (full CRUD)
# ============================================================

@app.route("/admin/invigilators")
def admin_invigilators():
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    invigilators = connection.execute("SELECT * FROM invigilators ORDER BY first_name").fetchall()
    connection.close()

    return render_template("invigilators.html", invigilators=invigilators)


@app.route("/admin/invigilators/add", methods=["GET", "POST"])
def add_invigilator():
    if not admin_required():
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("invigilator_form.html", invigilator=None)

    employee_number = request.form.get("employee_number")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    phone = request.form.get("phone")
    status = request.form.get("status")

    connection = get_db_connection()
    connection.execute("""
        INSERT INTO invigilators (employee_number, first_name, last_name, phone, status)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_number, first_name, last_name, phone, status))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_invigilators"))


@app.route("/admin/invigilators/edit/<int:invigilator_id>", methods=["GET", "POST"])
def edit_invigilator(invigilator_id):
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "GET":
        invigilator = connection.execute(
            "SELECT * FROM invigilators WHERE id = ?", (invigilator_id,)
        ).fetchone()
        connection.close()
        if invigilator is None:
            return redirect(url_for("admin_invigilators"))
        return render_template("invigilator_form.html", invigilator=invigilator)

    employee_number = request.form.get("employee_number")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    phone = request.form.get("phone")
    status = request.form.get("status")

    connection.execute("""
        UPDATE invigilators
        SET employee_number = ?, first_name = ?, last_name = ?, phone = ?, status = ?
        WHERE id = ?
    """, (employee_number, first_name, last_name, phone, status, invigilator_id))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_invigilators"))


@app.route("/admin/invigilators/delete/<int:invigilator_id>", methods=["POST"])
def delete_invigilator(invigilator_id):
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    connection.execute("DELETE FROM invigilators WHERE id = ?", (invigilator_id,))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_invigilators"))


# ============================================================
# INCIDENT MANAGEMENT (full CRUD)
# ============================================================

@app.route("/admin/incidents")
def admin_incidents():
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    incidents = connection.execute("""
        SELECT incidents.*, students.student_number, students.first_name, students.last_name,
               examinations.course_code
        FROM incidents
        LEFT JOIN students ON incidents.student_id = students.id
        LEFT JOIN examinations ON incidents.examination_id = examinations.id
        ORDER BY incidents.reported_at DESC
    """).fetchall()
    connection.close()

    return render_template("incidents.html", incidents=incidents)


@app.route("/admin/incidents/add", methods=["GET", "POST"])
def add_incident():
    if not admin_required() and not invigilator_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "GET":
        students = connection.execute("SELECT * FROM students ORDER BY first_name").fetchall()
        examinations = connection.execute("SELECT * FROM examinations ORDER BY examination_date DESC").fetchall()
        connection.close()
        return render_template("incident_form.html", students=students, examinations=examinations)

    student_id = request.form.get("student_id")
    examination_id = request.form.get("examination_id")
    incident_type = request.form.get("incident_type")
    description = request.form.get("description")
    severity = request.form.get("severity")

    connection.execute("""
        INSERT INTO incidents (student_id, examination_id, incident_type, description, severity, status)
        VALUES (?, ?, ?, ?, ?, 'open')
    """, (student_id, examination_id, incident_type, description, severity))
    connection.commit()
    connection.close()

    if admin_required():
        return redirect(url_for("admin_incidents"))
    return redirect(url_for("invigilator_dashboard"))


@app.route("/admin/incidents/resolve/<int:incident_id>", methods=["POST"])
def resolve_incident(incident_id):
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    connection.execute("UPDATE incidents SET status = 'resolved' WHERE id = ?", (incident_id,))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_incidents"))


@app.route("/admin/incidents/delete/<int:incident_id>", methods=["POST"])
def delete_incident(incident_id):
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()
    connection.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
    connection.commit()
    connection.close()

    return redirect(url_for("admin_incidents"))


# ============================================================
# REPORTS
# ============================================================

@app.route("/admin/reports")
def admin_reports():
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    by_severity = connection.execute("""
        SELECT severity, COUNT(*) AS total FROM incidents GROUP BY severity
    """).fetchall()

    by_status = connection.execute("""
        SELECT status, COUNT(*) AS total FROM incidents GROUP BY status
    """).fetchall()

    by_course = connection.execute("""
        SELECT examinations.course_code, COUNT(*) AS total
        FROM incidents
        JOIN examinations ON incidents.examination_id = examinations.id
        GROUP BY examinations.course_code
        ORDER BY total DESC
    """).fetchall()

    connection.close()

    return render_template(
        "reports.html",
        by_severity=by_severity,
        by_status=by_status,
        by_course=by_course
    )


# ============================================================
# AI ANALYSIS
# A simple, explainable rule-based flagging engine:
#   - Flags a student as "high risk" once they have 2+ incidents.
#   - Flags a student as "critical" once they have any 'high' severity incident.
# This is intentionally rule-based (not a trained ML model) so every
# flag can be explained in the presentation: it's a starting point the
# report identifies as extendable to a trained model later.
# ============================================================

@app.route("/admin/ai-analysis")
def admin_ai_analysis():
    if not admin_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    rows = connection.execute("""
        SELECT students.id, students.student_number, students.first_name, students.last_name,
               COUNT(incidents.id) AS incident_count,
               SUM(CASE WHEN incidents.severity = 'high' THEN 1 ELSE 0 END) AS high_severity_count
        FROM students
        JOIN incidents ON incidents.student_id = students.id
        GROUP BY students.id
        HAVING incident_count >= 1
        ORDER BY incident_count DESC
    """).fetchall()

    connection.close()

    flagged = []
    for row in rows:
        if row["high_severity_count"] and row["high_severity_count"] > 0:
            risk_level = "Critical"
        elif row["incident_count"] >= 2:
            risk_level = "High"
        else:
            risk_level = "Watch"
        flagged.append({
            "student_number": row["student_number"],
            "name": f'{row["first_name"]} {row["last_name"]}',
            "incident_count": row["incident_count"],
            "high_severity_count": row["high_severity_count"],
            "risk_level": risk_level
        })

    return render_template("ai_analysis.html", flagged=flagged)


# ============================================================
# SETTINGS
# ============================================================

@app.route("/admin/settings")
def admin_settings():
    if not admin_required():
        return redirect(url_for("login"))

    return render_template("settings.html", username=session.get("username"))


# ============================================================
# INVIGILATOR DASHBOARD
# ============================================================

@app.route("/invigilator")
def invigilator_dashboard():
    if not invigilator_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    invigilator = connection.execute(
        "SELECT * FROM invigilators WHERE user_id = ?", (session["user_id"],)
    ).fetchone()

    assigned_exams = []
    if invigilator is not None:
        assigned_exams = connection.execute("""
            SELECT * FROM examinations
            WHERE invigilator_id = ?
            ORDER BY examination_date, start_time
        """, (invigilator["id"],)).fetchall()

    connection.close()

    return render_template(
        "invigilator_dashboard.html",
        invigilator=invigilator,
        assigned_exams=assigned_exams
    )


if __name__ == "__main__":
    app.run(debug=True)
