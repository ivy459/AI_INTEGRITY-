import sqlite3
import os
from werkzeug.security import generate_password_hash


# ==========================================
# DATABASE LOCATION
# ==========================================

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "exam_integrity.db"
)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# CREATE DATABASE TABLES
# ==========================================

def create_tables():

    connection = get_db_connection()

    cursor = connection.cursor()

    # ======================================
    # USERS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================
    # STUDENTS
    # ======================================

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

    # ======================================
    # EXAMINATIONS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            examination_name TEXT NOT NULL,
            examination_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            venue TEXT NOT NULL,
            status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================
    # INVIGILATORS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invigilators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            employee_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    # ======================================
    # INCIDENTS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            examination_id INTEGER,
            incident_type TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'low',
            status TEXT DEFAULT 'open',
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id)
                REFERENCES students(id),
            FOREIGN KEY (examination_id)
                REFERENCES examinations(id)
        )
    """)

    connection.commit()

    connection.close()


# ==========================================
# CREATE ADMIN ACCOUNT
# ==========================================

def create_admin():

    connection = get_db_connection()

    cursor = connection.cursor()

    password = generate_password_hash(
        "Admin@123"
    )

    try:

        cursor.execute("""
            INSERT INTO users
            (username, password, role)
            VALUES (?, ?, ?)
        """, (
            "admin",
            password,
            "admin"
        ))

        connection.commit()

        print("Admin account created successfully!")

    except sqlite3.IntegrityError:

        print("Admin account already exists.")

    finally:

        connection.close()


# ==========================================
# ADD SAMPLE STUDENTS
# ==========================================

def create_sample_students():

    connection = get_db_connection()

    cursor = connection.cursor()

    students = [

        (
            "STU001",
            "Brian",
            "Otieno",
            "Bachelor of Information Science",
            3
        ),

        (
            "STU002",
            "Mary",
            "Achieng",
            "Business Information Management",
            2
        ),

        (
            "STU003",
            "David",
            "Omondi",
            "Computer Science",
            4
        ),

        (
            "STU004",
            "Grace",
            "Atieno",
            "Information Technology",
            3
        ),

        (
            "STU005",
            "Kevin",
            "Odhiambo",
            "Business Information Management",
            2
        )

    ]

    for student in students:

        try:

            cursor.execute("""
                INSERT INTO students
                (
                    student_number,
                    first_name,
                    last_name,
                    course,
                    year_of_study
                )
                VALUES (?, ?, ?, ?, ?)
            """, student)

        except sqlite3.IntegrityError:

            pass

    connection.commit()

    connection.close()

    print("Sample students added.")


# ==========================================
# ADD SAMPLE EXAMINATIONS
# ==========================================

def create_sample_examinations():

    connection = get_db_connection()

    cursor = connection.cursor()

    examinations = [

        (
            "COMP 321",
            "Database Systems",
            "2026-09-05",
            "08:00",
            "10:00",
            "LH1",
            "ongoing"
        ),

        (
            "BINM 331",
            "Systems Analysis and Design",
            "2026-09-05",
            "10:00",
            "12:00",
            "LH7",
            "upcoming"
        ),

        (
            "MATH 241",
            "Mathematics",
            "2026-09-05",
            "14:00",
            "16:00",
            "TC23",
            "upcoming"
        ),

        (
            "COMS 302",
            "Computer Networks",
            "2026-09-05",
            "16:00",
            "18:00",
            "C31",
            "upcoming"
        )

    ]

    for exam in examinations:

        cursor.execute("""
            SELECT id
            FROM examinations
            WHERE course_code = ?
            AND examination_date = ?
        """, (
            exam[0],
            exam[2]
        ))

        existing_exam = cursor.fetchone()

        if existing_exam is None:

            cursor.execute("""
                INSERT INTO examinations
                (
                    course_code,
                    examination_name,
                    examination_date,
                    start_time,
                    end_time,
                    venue,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, exam)

    connection.commit()

    connection.close()

    print("Sample examinations added.")


# ==========================================
# ADD SAMPLE INVIGILATORS
# ==========================================

def create_sample_invigilators():

    connection = get_db_connection()

    cursor = connection.cursor()

    invigilators = [

        (
            "INV001",
            "Peter",
            "Ochieng",
            "0712345678",
            "active"
        ),

        (
            "INV002",
            "Jane",
            "Akinyi",
            "0723456789",
            "active"
        ),

        (
            "INV003",
            "Samuel",
            "Okello",
            "0734567890",
            "active"
        )

    ]

    for invigilator in invigilators:

        try:

            cursor.execute("""
                INSERT INTO invigilators
                (
                    employee_number,
                    first_name,
                    last_name,
                    phone,
                    status
                )
                VALUES (?, ?, ?, ?, ?)
            """, invigilator)

        except sqlite3.IntegrityError:

            pass

    connection.commit()

    connection.close()

    print("Sample invigilators added.")


# ==========================================
# ADD SAMPLE INCIDENTS
# ==========================================

def create_sample_incidents():

    connection = get_db_connection()

    cursor = connection.cursor()

    # Get a student
    student = cursor.execute("""
        SELECT id
        FROM students
        LIMIT 1
    """).fetchone()

    # Get an examination
    examination = cursor.execute("""
        SELECT id
        FROM examinations
        LIMIT 1
    """).fetchone()

    if student and examination:

        incidents = [

            (
                student["id"],
                examination["id"],
                "Unauthorized device",
                "An unauthorized electronic device was detected.",
                "medium",
                "open"
            ),

            (
                student["id"],
                examination["id"],
                "Suspicious activity",
                "AI monitoring detected unusual examination activity.",
                "high",
                "open"
            ),

            (
                student["id"],
                examination["id"],
                "Identity verification",
                "Additional identity verification was requested.",
                "low",
                "resolved"
            )

        ]

        for incident in incidents:

            cursor.execute("""
                SELECT id
                FROM incidents
                WHERE student_id = ?
                AND examination_id = ?
                AND incident_type = ?
            """, (
                incident[0],
                incident[1],
                incident[2]
            ))

            existing_incident = cursor.fetchone()

            if existing_incident is None:

                cursor.execute("""
                    INSERT INTO incidents
                    (
                        student_id,
                        examination_id,
                        incident_type,
                        description,
                        severity,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, incident)

    connection.commit()

    connection.close()

    print("Sample incidents added.")


# ==========================================
# MAIN DATABASE SETUP
# ==========================================

if __name__ == "__main__":

    create_tables()

    create_admin()

    create_sample_students()

    create_sample_examinations()

    create_sample_invigilators()

    create_sample_incidents()

    print()
    print("======================================")
    print("DATABASE SETUP COMPLETED SUCCESSFULLY")
    print("======================================")