"""
database.py

Creates the SQLite schema for the AI Exam Integrity System and seeds it
with a small set of sample data so the app is demoable immediately.

Run this file directly whenever you need to (re)build the database:
    python database/database.py
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "exam_integrity.db")


def create_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'invigilator')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            course TEXT,
            year_of_study INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invigilators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            employee_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            examination_name TEXT NOT NULL,
            examination_date DATE NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            venue TEXT,
            invigilator_id INTEGER,
            status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'ongoing', 'completed', 'cancelled')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invigilator_id) REFERENCES invigilators (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            examination_id INTEGER,
            incident_type TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'low' CHECK (severity IN ('low', 'medium', 'high')),
            status TEXT DEFAULT 'open' CHECK (status IN ('open', 'resolved')),
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (examination_id) REFERENCES examinations (id)
        )
    """)


def seed_data(cursor):
    # --- Users ---------------------------------------------------------
    admin_hash = generate_password_hash("Admin@123")
    invig_hash = generate_password_hash("Invig@123")

    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, 'admin')
    """, ("admin", admin_hash))

    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, 'invigilator')
    """, ("jkamau", invig_hash))

    cursor.execute("SELECT id FROM users WHERE username = 'jkamau'")
    invig_user_id = cursor.fetchone()[0]

    # --- Invigilators ----------------------------------------------------
    cursor.execute("""
        INSERT OR IGNORE INTO invigilators
            (user_id, employee_number, first_name, last_name, phone, status)
        VALUES (?, 'EMP-001', 'James', 'Kamau', '0712345678', 'active')
    """, (invig_user_id,))

    cursor.execute("""
        INSERT OR IGNORE INTO invigilators
            (employee_number, first_name, last_name, phone, status)
        VALUES ('EMP-002', 'Faith', 'Wanjiru', '0723456789', 'active')
    """)

    # --- Students --------------------------------------------------------
    students = [
        ("CS/001/23", "Brian", "Otieno", "Computer Science", 2),
        ("CS/002/23", "Grace", "Njeri", "Computer Science", 2),
        ("BIT/014/22", "Kevin", "Mwangi", "Information Technology", 3),
        ("CS/045/24", "Aisha", "Hassan", "Computer Science", 1),
        ("BBIT/009/22", "Dennis", "Kiplagat", "Business IT", 3),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO students
            (student_number, first_name, last_name, course, year_of_study)
        VALUES (?, ?, ?, ?, ?)
    """, students)

    # --- Examinations ------------------------------------------------------
    exams = [
        ("CS201", "Data Structures & Algorithms", "2026-10-02", "09:00", "11:00", "Hall A", 1, "scheduled"),
        ("CS305", "Database Systems", "2026-10-03", "09:00", "11:00", "Hall B", 2, "scheduled"),
        ("CS210", "Operating Systems", "2026-09-26", "14:00", "16:00", "Hall A", 1, "ongoing"),
        ("BIT150", "Web Programming", "2026-09-20", "09:00", "11:00", "Hall C", 2, "completed"),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO examinations
            (course_code, examination_name, examination_date, start_time, end_time, venue, invigilator_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, exams)

    # --- Incidents ---------------------------------------------------------
    cursor.execute("SELECT id FROM students WHERE student_number = 'CS/001/23'")
    s1 = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM students WHERE student_number = 'BIT/014/22'")
    s2 = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM examinations WHERE course_code = 'BIT150'")
    e1 = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM examinations WHERE course_code = 'CS210'")
    e2 = cursor.fetchone()[0]

    incidents = [
        (s1, e1, "Unauthorized material", "Found with handwritten notes in exam hall.", "high", "open"),
        (s2, e1, "Phone use", "Phone seen under the desk during exam.", "medium", "resolved"),
        (s1, e2, "Talking", "Communicating with another candidate.", "low", "open"),
    ]
    cursor.executemany("""
        INSERT INTO incidents
            (student_id, examination_id, incident_type, description, severity, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, incidents)


def build_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    create_tables(cursor)
    seed_data(cursor)

    connection.commit()
    connection.close()
    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    build_database()
