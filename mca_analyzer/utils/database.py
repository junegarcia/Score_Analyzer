"""
Oracle Database Utility
Handles connection pooling, schema creation, seeding, and all CRUD/analytics
operations. Uses python-oracledb in thin mode, so no Oracle Instant Client
install is required for a plain host:port/service_name connection.
"""

import oracledb
import os
import random
import hashlib
from datetime import datetime
from contextlib import contextmanager

# ──────────────────────────────────────────────
#  CONNECTION
# ──────────────────────────────────────────────
ORACLE_HOST    = os.getenv("ORACLE_HOST", "localhost")
ORACLE_PORT    = os.getenv("ORACLE_PORT", "1521")
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE", "XEPDB1")   # e.g. XEPDB1 for Oracle XE
ORACLE_USER    = os.getenv("ORACLE_USER", "student")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "1j2u3n4e")

DSN = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=DSN,
            min=2, max=10, increment=1,
        )
    return _pool


@contextmanager
def get_cursor(commit: bool = False):
    """Yields a cursor from a pooled connection; commits on request."""
    pool = get_pool()
    conn = pool.acquire()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        pool.release(conn)


def check_connection():
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM dual")
            cur.fetchone()
        return True, "Connected"
    except Exception as e:
        return False, str(e)


def _rows_as_dicts(cur):
    cols = [c[0].lower() for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _row_as_dict(cur, row):
    if row is None:
        return None
    cols = [c[0].lower() for c in cur.description]
    return dict(zip(cols, row))


# ──────────────────────────────────────────────
#  PASSWORD HELPERS
# ──────────────────────────────────────────────
def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ──────────────────────────────────────────────
#  AUTHENTICATION
# ──────────────────────────────────────────────
def authenticate_user(username: str, password: str, role: str):
    """Returns user dict or None."""
    table_map = {"student": "students", "teacher": "teachers", "admin": "admins"}
    table = table_map.get(role)
    if table is None:
        return None

    with get_cursor() as cur:
        cur.execute(f"SELECT * FROM {table} WHERE username = :username", {"username": username})
        row = cur.fetchone()
        user = _row_as_dict(cur, row)

    if user and verify_password(password, user["password"]):
        return user
    return None


# ──────────────────────────────────────────────
#  SUBJECTS
# ──────────────────────────────────────────────
SUBJECTS = {
    1: ["Data Structures", "Database Management", "Computer Networks", "Programming in Python"],
    2: ["Operating Systems", "Software Engineering", "Web Technologies", "Discrete Mathematics"],
    3: ["Machine Learning", "Cloud Computing", "Cyber Security", "Advanced Java"],
    4: ["Big Data Analytics", "Project Work", "Advanced Algorithms", "Research Methodology"],
}


def get_subjects_by_semester(semester: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM subjects WHERE semester = :sem ORDER BY code", {"sem": semester})
        return _rows_as_dicts(cur)


def get_all_subjects():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM subjects ORDER BY semester, code")
        return _rows_as_dicts(cur)


def get_subject_by_code(code: str):
    """Replaces the old `get_db().subjects.find_one({'code': code})` pattern."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM subjects WHERE code = :code", {"code": code})
        return _row_as_dict(cur, cur.fetchone())


def add_subject(data: dict) -> tuple[bool, str]:
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT COUNT(*) FROM subjects WHERE code = :c", {"c": data["code"]})
        if cur.fetchone()[0] > 0:
            return False, "Subject code already exists."

        cur.execute("""
            INSERT INTO subjects (subject_id, code, name, semester, max_marks)
            VALUES (:subject_id, :code, :name, :semester, :max_marks)
        """, {
            "subject_id": data["subject_id"],
            "code":       data["code"],
            "name":       data["name"],
            "semester":   data["semester"],
            "max_marks":  data.get("max_marks", 100),
        })
    return True, "Subject added successfully."


def update_subject(subject_id: str, updates: dict) -> tuple[bool, str]:
    if not updates:
        return False, "No changes made."

    with get_cursor(commit=True) as cur:
        # If code is changing, make sure the new code isn't already taken
        # by a different subject.
        if "code" in updates:
            cur.execute("""
                SELECT COUNT(*) FROM subjects
                WHERE code = :c AND subject_id != :sid
            """, {"c": updates["code"], "sid": subject_id})
            if cur.fetchone()[0] > 0:
                return False, "Subject code already exists."

        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        params = dict(updates)
        params["sid"] = subject_id

        cur.execute(f"""
            UPDATE subjects SET {set_clause}
            WHERE subject_id = :sid
        """, params)
        if cur.rowcount:
            return True, "Subject updated."
    return False, "No changes made."


def delete_subject(subject_id: str) -> tuple[bool, str]:
    with get_cursor(commit=True) as cur:
        # Look up the code first, since marks/teachers reference subjects by code.
        cur.execute("SELECT code FROM subjects WHERE subject_id = :sid", {"sid": subject_id})
        row = cur.fetchone()
        if not row:
            return False, "Subject not found."
        code = row[0]

        cur.execute("SELECT COUNT(*) FROM marks WHERE subject_code = :c", {"c": code})
        marks_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM teachers WHERE subject_code = :c", {"c": code})
        teachers_count = cur.fetchone()[0]

        if marks_count or teachers_count:
            return False, (
                f"Cannot delete: {marks_count} mark record(s) and "
                f"{teachers_count} teacher(s) still reference this subject. "
                f"Reassign or remove them first."
            )

        cur.execute("DELETE FROM subjects WHERE subject_id = :sid", {"sid": subject_id})
        if cur.rowcount:
            return True, "Subject deleted."
    return False, "Subject not found."


# ──────────────────────────────────────────────
#  STUDENTS
# ──────────────────────────────────────────────
def get_all_students():
    with get_cursor() as cur:
        cur.execute("""
            SELECT student_id, name, username, roll_number, section, year,
                   semester, email, created_at
            FROM students ORDER BY roll_number
        """)
        return _rows_as_dicts(cur)


def get_students_by_section(section: str):
    with get_cursor() as cur:
        cur.execute("""
            SELECT student_id, name, username, roll_number, section, year,
                   semester, email, created_at
            FROM students WHERE section = :section ORDER BY roll_number
        """, {"section": section})
        return _rows_as_dicts(cur)


def get_student_by_username(username: str):
    with get_cursor() as cur:
        cur.execute("""
            SELECT student_id, name, username, roll_number, section, year,
                   semester, email, created_at
            FROM students WHERE username = :username
        """, {"username": username})
        return _row_as_dict(cur, cur.fetchone())


def get_student_by_id(student_id: str):
    with get_cursor() as cur:
        cur.execute("""
            SELECT student_id, name, username, roll_number, section, year,
                   semester, email, created_at
            FROM students WHERE student_id = :sid
        """, {"sid": student_id})
        return _row_as_dict(cur, cur.fetchone())


def add_student(data: dict) -> tuple[bool, str]:
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT COUNT(*) FROM students WHERE username = :u", {"u": data["username"]})
        if cur.fetchone()[0] > 0:
            return False, "Username already exists."
        cur.execute("SELECT COUNT(*) FROM students WHERE roll_number = :r", {"r": data["roll_number"]})
        if cur.fetchone()[0] > 0:
            return False, "Roll number already exists."

        cur.execute("""
            INSERT INTO students
                (student_id, name, username, password, roll_number,
                 section, year, semester, email, created_at)
            VALUES
                (:student_id, :name, :username, :password, :roll_number,
                 :section, :year, :semester, :email, SYSTIMESTAMP)
        """, {
            "student_id": data["student_id"],
            "name": data["name"],
            "username": data["username"],
            "password": hash_password(data["password"]),
            "roll_number": data["roll_number"],
            "section": data["section"],
            "year": data["year"],
            "semester": data["semester"],
            "email": data.get("email", ""),
        })
    return True, "Student added successfully."


def update_student(student_id: str, updates: dict) -> tuple[bool, str]:
    updates = dict(updates)
    if "password" in updates:
        if updates["password"]:
            updates["password"] = hash_password(updates["password"])
        else:
            del updates["password"]

    if not updates:
        return False, "No changes made."

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    params = dict(updates)
    params["sid"] = student_id

    with get_cursor(commit=True) as cur:
        cur.execute(f"""
            UPDATE students SET {set_clause}, updated_at = SYSTIMESTAMP
            WHERE student_id = :sid
        """, params)
        if cur.rowcount:
            return True, "Student updated."
    return False, "No changes made."


def delete_student(student_id: str) -> tuple[bool, str]:
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM marks WHERE student_id = :sid", {"sid": student_id})
        cur.execute("DELETE FROM students WHERE student_id = :sid", {"sid": student_id})
        if cur.rowcount:
            return True, "Student deleted."
    return False, "Student not found."


# ──────────────────────────────────────────────
#  TEACHERS
# ──────────────────────────────────────────────
def get_all_teachers():
    with get_cursor() as cur:
        cur.execute("""
            SELECT teacher_id, name, username, subject_code, section, email, created_at
            FROM teachers ORDER BY name
        """)
        return _rows_as_dicts(cur)


def get_teacher_by_username(username: str):
    with get_cursor() as cur:
        cur.execute("""
            SELECT teacher_id, name, username, subject_code, section, email, created_at
            FROM teachers WHERE username = :username
        """, {"username": username})
        return _row_as_dict(cur, cur.fetchone())


def add_teacher(data: dict) -> tuple[bool, str]:
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT COUNT(*) FROM teachers WHERE username = :u", {"u": data["username"]})
        if cur.fetchone()[0] > 0:
            return False, "Username already exists."

        cur.execute("""
            INSERT INTO teachers
                (teacher_id, name, username, password, subject_code, section, email, created_at)
            VALUES
                (:teacher_id, :name, :username, :password, :subject_code, :section, :email, SYSTIMESTAMP)
        """, {
            "teacher_id": data["teacher_id"],
            "name": data["name"],
            "username": data["username"],
            "password": hash_password(data["password"]),
            "subject_code": data["subject_code"],
            "section": data["section"],
            "email": data.get("email", ""),
        })
    return True, "Teacher added successfully."


def update_teacher(teacher_id: str, updates: dict) -> tuple[bool, str]:
    updates = dict(updates)
    if "password" in updates:
        if updates["password"]:
            updates["password"] = hash_password(updates["password"])
        else:
            del updates["password"]

    if not updates:
        return False, "No changes made."

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    params = dict(updates)
    params["tid"] = teacher_id

    with get_cursor(commit=True) as cur:
        cur.execute(f"""
            UPDATE teachers SET {set_clause}, updated_at = SYSTIMESTAMP
            WHERE teacher_id = :tid
        """, params)
        if cur.rowcount:
            return True, "Teacher updated."
    return False, "No changes made."


def delete_teacher(teacher_id: str) -> tuple[bool, str]:
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM teachers WHERE teacher_id = :tid", {"tid": teacher_id})
        if cur.rowcount:
            return True, "Teacher deleted."
    return False, "Teacher not found."


def assign_subject_to_teacher(teacher_id: str, subject_code: str, section: str) -> tuple[bool, str]:
    with get_cursor(commit=True) as cur:
        cur.execute("""
            UPDATE teachers SET subject_code = :sub, section = :sec, updated_at = SYSTIMESTAMP
            WHERE teacher_id = :tid
        """, {"sub": subject_code, "sec": section, "tid": teacher_id})
        if cur.rowcount:
            return True, "Subject assigned."
    return False, "Teacher not found."


# ──────────────────────────────────────────────
#  MARKS
# ──────────────────────────────────────────────
def get_marks_by_student(student_id: str):
    with get_cursor() as cur:
        cur.execute("""
            SELECT student_id, subject_code, semester, marks_obtained, max_marks
            FROM marks WHERE student_id = :sid
        """, {"sid": student_id})
        return _rows_as_dicts(cur)


def get_mark(student_id: str, subject_code: str, semester: int):
    """Replaces the old `get_db().marks.find_one({...})` pattern."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT marks_obtained, max_marks FROM marks
            WHERE student_id = :sid AND subject_code = :sub AND semester = :sem
        """, {"sid": student_id, "sub": subject_code, "sem": semester})
        return _row_as_dict(cur, cur.fetchone())


def get_marks_by_subject_section(subject_code: str, section: str, semester: int):
    with get_cursor() as cur:
        cur.execute("""
            SELECT mk.student_id, st.name AS student_name, st.roll_number,
                   mk.marks_obtained, mk.max_marks, mk.subject_code, mk.semester
            FROM marks mk
            JOIN students st ON st.student_id = mk.student_id
            WHERE mk.subject_code = :sub AND mk.semester = :sem AND st.section = :sec
            ORDER BY st.roll_number
        """, {"sub": subject_code, "sem": semester, "sec": section})
        return _rows_as_dicts(cur)


def upsert_mark(student_id: str, subject_code: str, semester: int,
                 marks_obtained: float, max_marks: int = 100) -> tuple[bool, str]:
    if not (0 <= marks_obtained <= max_marks):
        return False, f"Marks must be between 0 and {max_marks}."

    with get_cursor(commit=True) as cur:
        cur.execute("""
            MERGE INTO marks m
            USING (SELECT :sid AS student_id, :sub AS subject_code, :sem AS semester FROM dual) src
               ON (m.student_id = src.student_id AND m.subject_code = src.subject_code
                   AND m.semester = src.semester)
            WHEN MATCHED THEN
                UPDATE SET marks_obtained = :marks, max_marks = :maxm, updated_at = SYSTIMESTAMP
            WHEN NOT MATCHED THEN
                INSERT (student_id, subject_code, semester, marks_obtained, max_marks, updated_at)
                VALUES (:sid, :sub, :sem, :marks, :maxm, SYSTIMESTAMP)
        """, {
            "sid": student_id, "sub": subject_code, "sem": semester,
            "marks": marks_obtained, "maxm": max_marks,
        })
    return True, "Mark saved."


def bulk_upsert_marks(records: list) -> tuple[int, int]:
    """records: list of dicts with student_id, subject_code, semester, marks_obtained"""
    success, fail = 0, 0
    for r in records:
        ok, _ = upsert_mark(r["student_id"], r["subject_code"],
                             r["semester"], float(r["marks_obtained"]))
        if ok:
            success += 1
        else:
            fail += 1
    return success, fail


# ──────────────────────────────────────────────
#  ANALYTICS
# ──────────────────────────────────────────────
def calculate_student_analytics(student_id: str, semester: int):
    """Returns percentage, marks list and subject-wise data for a student."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT mk.student_id, mk.subject_code, mk.semester,
                   mk.marks_obtained, mk.max_marks, sub.name AS subject_name
            FROM marks mk
            JOIN subjects sub ON sub.code = mk.subject_code
            WHERE mk.student_id = :sid AND mk.semester = :sem
        """, {"sid": student_id, "sem": semester})
        marks = _rows_as_dicts(cur)

    if not marks:
        return None

    total_obtained = sum(m["marks_obtained"] for m in marks)
    total_max = sum(m.get("max_marks", 100) for m in marks)
    percentage = round((total_obtained / total_max) * 100, 2) if total_max else 0

    return {
        "marks": marks,
        "total_obtained": total_obtained,
        "total_max": total_max,
        "percentage": percentage,
    }


def calculate_semester_ranks(semester: int, section: str = None):
    """Returns sorted list of dicts with student_id, name, percentage, rank."""
    query = """
        SELECT student_id, name, roll_number, section,
               total_obtained, total_max, percentage,
               RANK() OVER (ORDER BY percentage DESC) AS rnk
        FROM (
            SELECT st.student_id, st.name, st.roll_number, st.section,
                   SUM(mk.marks_obtained) AS total_obtained,
                   SUM(mk.max_marks)      AS total_max,
                   ROUND(SUM(mk.marks_obtained) / SUM(mk.max_marks) * 100, 2) AS percentage
            FROM marks mk
            JOIN students st ON st.student_id = mk.student_id
            WHERE mk.semester = :sem
              AND (:section IS NULL OR st.section = :section)
            GROUP BY st.student_id, st.name, st.roll_number, st.section
        )
        ORDER BY percentage DESC
    """
    with get_cursor() as cur:
        cur.execute(query, {"sem": semester, "section": section})
        results = _rows_as_dicts(cur)

    for r in results:
        r["rank"] = r.pop("rnk")
    return results


def get_subject_averages(semester: int, section: str = None):
    query = """
        SELECT mk.subject_code AS code, sub.name AS subject_name,
               AVG(mk.marks_obtained) AS avg_marks,
               MIN(mk.max_marks)      AS max_marks,
               COUNT(*)               AS count
        FROM marks mk
        JOIN subjects sub ON sub.code = mk.subject_code
        JOIN students st  ON st.student_id = mk.student_id
        WHERE mk.semester = :sem
          AND (:section IS NULL OR st.section = :section)
        GROUP BY mk.subject_code, sub.name
        ORDER BY mk.subject_code
    """
    with get_cursor() as cur:
        cur.execute(query, {"sem": semester, "section": section})
        results = _rows_as_dicts(cur)

    for r in results:
        r["_id"] = r["code"]
        r["avg_percentage"] = round((r["avg_marks"] / r["max_marks"]) * 100, 2) if r["max_marks"] else 0
    return results


def get_admin_overview():
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM students")
        total_students = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM teachers")
        total_teachers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM marks")
        total_marks = cur.fetchone()[0]

        section_counts = {}
        for sec in ["A", "B", "C", "D"]:
            cur.execute("SELECT COUNT(*) FROM students WHERE section = :sec", {"sec": sec})
            section_counts[sec] = cur.fetchone()[0]

    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_marks": total_marks,
        "section_counts": section_counts,
    }


# ──────────────────────────────────────────────
#  SCHEMA
# ──────────────────────────────────────────────
_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE admins (
        admin_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        name         VARCHAR2(100) NOT NULL,
        username     VARCHAR2(50)  NOT NULL UNIQUE,
        password     VARCHAR2(100) NOT NULL,
        email        VARCHAR2(100),
        created_at   TIMESTAMP DEFAULT SYSTIMESTAMP
    )
    """,
    """
    CREATE TABLE subjects (
        subject_id   VARCHAR2(20)  PRIMARY KEY,
        code         VARCHAR2(20)  NOT NULL UNIQUE,
        name         VARCHAR2(100) NOT NULL,
        semester     NUMBER(1)     NOT NULL,
        max_marks    NUMBER(5)     DEFAULT 100
    )
    """,
    """
    CREATE TABLE students (
        student_id   VARCHAR2(20)  PRIMARY KEY,
        name         VARCHAR2(100) NOT NULL,
        username     VARCHAR2(50)  NOT NULL UNIQUE,
        password     VARCHAR2(100) NOT NULL,
        roll_number  VARCHAR2(20)  NOT NULL UNIQUE,
        section      VARCHAR2(1)   NOT NULL,
        year         NUMBER(1)     NOT NULL,
        semester     NUMBER(1)     NOT NULL,
        email        VARCHAR2(100),
        created_at   TIMESTAMP DEFAULT SYSTIMESTAMP,
        updated_at   TIMESTAMP
    )
    """,
    """
    CREATE TABLE teachers (
        teacher_id   VARCHAR2(20)  PRIMARY KEY,
        name         VARCHAR2(100) NOT NULL,
        username     VARCHAR2(50)  NOT NULL UNIQUE,
        password     VARCHAR2(100) NOT NULL,
        subject_code VARCHAR2(20)  REFERENCES subjects(code),
        section      VARCHAR2(1)   NOT NULL,
        email        VARCHAR2(100),
        created_at   TIMESTAMP DEFAULT SYSTIMESTAMP,
        updated_at   TIMESTAMP
    )
    """,
    """
    CREATE TABLE marks (
        student_id     VARCHAR2(20) REFERENCES students(student_id),
        subject_code   VARCHAR2(20) REFERENCES subjects(code),
        semester       NUMBER(1)    NOT NULL,
        marks_obtained NUMBER(5,2)  NOT NULL,
        max_marks      NUMBER(5)    DEFAULT 100,
        updated_at     TIMESTAMP DEFAULT SYSTIMESTAMP,
        CONSTRAINT pk_marks PRIMARY KEY (student_id, subject_code, semester)
    )
    """,
]


def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM user_tables WHERE table_name = :t",
        {"t": table_name.upper()},
    )
    return cur.fetchone()[0] > 0


def _create_schema_if_needed():
    with get_cursor(commit=True) as cur:
        for stmt in _SCHEMA_STATEMENTS:
            table_name = stmt.strip().split()[2]
            if not _table_exists(cur, table_name):
                cur.execute(stmt)


# ──────────────────────────────────────────────
#  SEED DATA
# ──────────────────────────────────────────────
def seed_database():
    _create_schema_if_needed()

    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM admins")
        if cur.fetchone()[0] > 0:
            return  # Already seeded

    print("🌱 Seeding database...")

    with get_cursor(commit=True) as cur:
        # Admin
        cur.execute("""
            INSERT INTO admins (name, username, password, email, created_at)
            VALUES (:name, :username, :password, :email, SYSTIMESTAMP)
        """, {
            "name": "Dr. Admin", "username": "admin",
            "password": hash_password("admin123"), "email": "admin@mca.edu",
        })

        # Subjects
        subjects_to_insert = []
        sub_id = 1
        for sem, names in SUBJECTS.items():
            for name in names:
                code = name[:2].upper() + str(sem) + str(sub_id).zfill(2)
                subjects_to_insert.append({
                    "subject_id": f"SUB{sub_id:03d}",
                    "code": code,
                    "name": name,
                    "semester": sem,
                    "max_marks": 100,
                })
                sub_id += 1
        cur.executemany("""
            INSERT INTO subjects (subject_id, code, name, semester, max_marks)
            VALUES (:subject_id, :code, :name, :semester, :max_marks)
        """, subjects_to_insert)

        # Students (4 sections × 10 = 40)
        sections = ["A", "B", "C", "D"]
        first_names = [
            "Aarav", "Bhavya", "Chirag", "Deepika", "Eshan",
            "Farhan", "Garima", "Harsh", "Ishaan", "Jaya",
            "Kiran", "Lata", "Mohan", "Neha", "Om",
            "Pooja", "Qasim", "Riya", "Suresh", "Tanya",
            "Uday", "Vani", "Wasim", "Xena", "Yash",
            "Zara", "Anil", "Beena", "Chandan", "Divya",
            "Ekta", "Firoz", "Geeta", "Hemant", "Isha",
            "Jagdish", "Kamla", "Lokesh", "Meera", "Nitin",
        ]
        last_names = ["Sharma", "Verma", "Gupta", "Singh", "Patel", "Mehta", "Kumar", "Joshi", "Rao", "Nair"]

        random.seed(42)
        students_to_insert = []
        marks_to_insert = []
        roll = 1001
        idx = 0

        for sec in sections:
            for i in range(10):
                fname = first_names[idx % len(first_names)]
                lname = random.choice(last_names)
                stu_id = f"STU{roll}"
                uname = f"{fname.lower()}{roll}"
                students_to_insert.append({
                    "student_id": stu_id,
                    "name": f"{fname} {lname}",
                    "username": uname,
                    "password": hash_password(f"pass{roll}"),
                    "roll_number": str(roll),
                    "section": sec,
                    "year": 1,
                    "semester": 1,
                    "email": f"{uname}@mca.edu",
                })
                for sub in subjects_to_insert:
                    marks_to_insert.append({
                        "student_id": stu_id,
                        "subject_code": sub["code"],
                        "semester": sub["semester"],
                        "marks_obtained": round(random.uniform(45, 98), 1),
                        "max_marks": 100,
                    })
                roll += 1
                idx += 1

        cur.executemany("""
            INSERT INTO students
                (student_id, name, username, password, roll_number, section, year, semester, email, created_at)
            VALUES
                (:student_id, :name, :username, :password, :roll_number, :section, :year, :semester, :email, SYSTIMESTAMP)
        """, students_to_insert)

        cur.executemany("""
            INSERT INTO marks (student_id, subject_code, semester, marks_obtained, max_marks, updated_at)
            VALUES (:student_id, :subject_code, :semester, :marks_obtained, :max_marks, SYSTIMESTAMP)
        """, marks_to_insert)

        # Teachers (one per subject, section A default)
        # NOTE: subjects are referenced by NAME here and resolved to their
        # generated `code` below, since subject codes are derived at seed
        # time (name[:2].upper() + semester + running id) and won't match
        # hand-typed codes like "DS101". The teachers.subject_code column
        # has a foreign key to subjects.code, so this must resolve correctly.
        code_by_name = {s["name"]: s["code"] for s in subjects_to_insert}
        teacher_data = [
            ("Prof. Anand Kumar",  "t_anand",  "Data Structures",        "A"),
            ("Prof. Bhavna Shah",  "t_bhavna", "Database Management",    "B"),
            ("Prof. Chetan Roy",   "t_chetan", "Computer Networks",      "C"),
            ("Prof. Divya Menon",  "t_divya",  "Operating Systems",      "D"),
            ("Prof. Esha Tiwari",  "t_esha",   "Software Engineering",   "A"),
            ("Prof. Farida Malik", "t_farida", "Web Technologies",       "B"),
            ("Prof. Ganesh Iyer",  "t_ganesh", "Machine Learning",       "C"),
            ("Prof. Hina Qureshi", "t_hina",   "Cloud Computing",        "D"),
            ("Prof. Inder Kapoor", "t_inder",  "Cyber Security",         "A"),
            ("Prof. Jaya Pillai",  "t_jaya",   "Big Data Analytics",     "B"),
            ("Prof. Karan Joshi",  "t_karan",  "Project Work",           "C"),
            ("Prof. Lata Saxena",  "t_lata",   "Advanced Algorithms",    "D"),
        ]
        teachers_to_insert = []
        for t_idx, (name, uname, subject_name, sec) in enumerate(teacher_data):
            teachers_to_insert.append({
                "teacher_id": f"TCH{t_idx+1:03d}",
                "name": name,
                "username": uname,
                "password": hash_password(f"tpass{t_idx+1}"),
                "subject_code": code_by_name[subject_name],
                "section": sec,
                "email": f"{uname}@mca.edu",
            })
        cur.executemany("""
            INSERT INTO teachers
                (teacher_id, name, username, password, subject_code, section, email, created_at)
            VALUES
                (:teacher_id, :name, :username, :password, :subject_code, :section, :email, SYSTIMESTAMP)
        """, teachers_to_insert)

    print("✅ Seeding complete.")