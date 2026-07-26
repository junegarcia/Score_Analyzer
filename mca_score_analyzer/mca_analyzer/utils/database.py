"""
MongoDB Database Utility
Handles connection, initialization, and all CRUD operations
"""

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
import os
from datetime import datetime
import random
import hashlib

# ──────────────────────────────────────────────
#  CONNECTION
# ──────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = "mca_analyzer"

_client = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client

def get_db():
    return get_client()[DB_NAME]

def check_connection():
    try:
        get_client().admin.command("ping")
        return True, "Connected"
    except Exception as e:
        return False, str(e)

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
    db = get_db()
    collection_map = {
        "student":     db.students,
        "teacher":     db.teachers,
        "admin":       db.admins,
    }
    col = collection_map.get(role)
    if col is None:
        return None
    user = col.find_one({"username": username})
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
    db = get_db()
    return list(db.subjects.find({"semester": semester}, {"_id": 0}))

def get_all_subjects():
    db = get_db()
    return list(db.subjects.find({}, {"_id": 0}).sort("semester", ASCENDING))

# ──────────────────────────────────────────────
#  STUDENTS
# ──────────────────────────────────────────────
def get_all_students():
    db = get_db()
    return list(db.students.find({}, {"password": 0}).sort("roll_number", ASCENDING))

def get_students_by_section(section: str):
    db = get_db()
    return list(db.students.find({"section": section}, {"password": 0}).sort("roll_number", ASCENDING))

def get_student_by_username(username: str):
    db = get_db()
    return db.students.find_one({"username": username}, {"password": 0})

def get_student_by_id(student_id: str):
    db = get_db()
    return db.students.find_one({"student_id": student_id}, {"password": 0})

def add_student(data: dict) -> tuple[bool, str]:
    db = get_db()
    if db.students.find_one({"username": data["username"]}):
        return False, "Username already exists."
    if db.students.find_one({"roll_number": data["roll_number"]}):
        return False, "Roll number already exists."
    data["password"] = hash_password(data["password"])
    data["created_at"] = datetime.utcnow()
    db.students.insert_one(data)
    return True, "Student added successfully."

def update_student(student_id: str, updates: dict) -> tuple[bool, str]:
    db = get_db()
    if "password" in updates and updates["password"]:
        updates["password"] = hash_password(updates["password"])
    elif "password" in updates:
        del updates["password"]
    updates["updated_at"] = datetime.utcnow()
    result = db.students.update_one({"student_id": student_id}, {"$set": updates})
    if result.modified_count:
        return True, "Student updated."
    return False, "No changes made."

def delete_student(student_id: str) -> tuple[bool, str]:
    db = get_db()
    db.marks.delete_many({"student_id": student_id})
    result = db.students.delete_one({"student_id": student_id})
    if result.deleted_count:
        return True, "Student deleted."
    return False, "Student not found."

# ──────────────────────────────────────────────
#  TEACHERS
# ──────────────────────────────────────────────
def get_all_teachers():
    db = get_db()
    return list(db.teachers.find({}, {"password": 0}).sort("name", ASCENDING))

def get_teacher_by_username(username: str):
    db = get_db()
    return db.teachers.find_one({"username": username}, {"password": 0})

def add_teacher(data: dict) -> tuple[bool, str]:
    db = get_db()
    if db.teachers.find_one({"username": data["username"]}):
        return False, "Username already exists."
    data["password"] = hash_password(data["password"])
    data["created_at"] = datetime.utcnow()
    db.teachers.insert_one(data)
    return True, "Teacher added successfully."

def update_teacher(teacher_id: str, updates: dict) -> tuple[bool, str]:
    db = get_db()
    if "password" in updates and updates["password"]:
        updates["password"] = hash_password(updates["password"])
    elif "password" in updates:
        del updates["password"]
    updates["updated_at"] = datetime.utcnow()
    result = db.teachers.update_one({"teacher_id": teacher_id}, {"$set": updates})
    if result.modified_count:
        return True, "Teacher updated."
    return False, "No changes made."

def delete_teacher(teacher_id: str) -> tuple[bool, str]:
    db = get_db()
    result = db.teachers.delete_one({"teacher_id": teacher_id})
    if result.deleted_count:
        return True, "Teacher deleted."
    return False, "Teacher not found."

def assign_subject_to_teacher(teacher_id: str, subject_code: str, section: str) -> tuple[bool, str]:
    db = get_db()
    result = db.teachers.update_one(
        {"teacher_id": teacher_id},
        {"$set": {"subject_code": subject_code, "section": section, "updated_at": datetime.utcnow()}}
    )
    if result.modified_count:
        return True, "Subject assigned."
    return False, "Teacher not found."

# ──────────────────────────────────────────────
#  MARKS
# ──────────────────────────────────────────────
def get_marks_by_student(student_id: str):
    db = get_db()
    return list(db.marks.find({"student_id": student_id}, {"_id": 0}))

def get_marks_by_subject_section(subject_code: str, section: str, semester: int):
    db = get_db()
    # Join with students to filter by section
    pipeline = [
        {"$match": {"subject_code": subject_code, "semester": semester}},
        {"$lookup": {
            "from": "students",
            "localField": "student_id",
            "foreignField": "student_id",
            "as": "student"
        }},
        {"$unwind": "$student"},
        {"$match": {"student.section": section}},
        {"$project": {
            "_id": 0,
            "student_id": 1,
            "student_name": "$student.name",
            "roll_number": "$student.roll_number",
            "marks_obtained": 1,
            "max_marks": 1,
            "subject_code": 1,
            "semester": 1,
        }}
    ]
    return list(db.marks.aggregate(pipeline))

def upsert_mark(student_id: str, subject_code: str, semester: int,
                marks_obtained: float, max_marks: int = 100) -> tuple[bool, str]:
    db = get_db()
    if not (0 <= marks_obtained <= max_marks):
        return False, f"Marks must be between 0 and {max_marks}."
    db.marks.update_one(
        {"student_id": student_id, "subject_code": subject_code, "semester": semester},
        {"$set": {
            "marks_obtained": marks_obtained,
            "max_marks": max_marks,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    return True, "Mark saved."

def bulk_upsert_marks(records: list) -> tuple[int, int]:
    """records: list of dicts with student_id, subject_code, semester, marks_obtained"""
    success, fail = 0, 0
    for r in records:
        ok, _ = upsert_mark(r["student_id"], r["subject_code"],
                            r["semester"], float(r["marks_obtained"]))
        if ok: success += 1
        else:  fail += 1
    return success, fail

# ──────────────────────────────────────────────
#  ANALYTICS
# ──────────────────────────────────────────────
def calculate_student_analytics(student_id: str, semester: int):
    """Returns percentage, marks list and subject-wise data for a student."""
    db = get_db()
    marks = list(db.marks.find(
        {"student_id": student_id, "semester": semester}, {"_id": 0}
    ))
    if not marks:
        return None

    total_obtained = sum(m["marks_obtained"] for m in marks)
    total_max      = sum(m.get("max_marks", 100) for m in marks)
    percentage     = round((total_obtained / total_max) * 100, 2) if total_max else 0

    # Attach subject names
    subjects = {s["code"]: s["name"] for s in db.subjects.find({}, {"_id": 0})}
    for m in marks:
        m["subject_name"] = subjects.get(m["subject_code"], m["subject_code"])

    return {
        "marks": marks,
        "total_obtained": total_obtained,
        "total_max": total_max,
        "percentage": percentage,
    }

def calculate_semester_ranks(semester: int, section: str = None):
    """Returns sorted list of (student_id, name, percentage, rank)."""
    db = get_db()
    pipeline = [
        {"$match": {"semester": semester}},
        {"$group": {
            "_id": "$student_id",
            "total_obtained": {"$sum": "$marks_obtained"},
            "total_max": {"$sum": "$max_marks"},
        }},
        {"$lookup": {
            "from": "students",
            "localField": "_id",
            "foreignField": "student_id",
            "as": "student"
        }},
        {"$unwind": "$student"},
    ]
    if section:
        pipeline.append({"$match": {"student.section": section}})

    pipeline += [
        {"$project": {
            "_id": 0,
            "student_id": "$_id",
            "name": "$student.name",
            "roll_number": "$student.roll_number",
            "section": "$student.section",
            "total_obtained": 1,
            "total_max": 1,
            "percentage": {
                "$round": [{"$multiply": [{"$divide": ["$total_obtained","$total_max"]}, 100]}, 2]
            }
        }},
        {"$sort": {"percentage": -1}}
    ]

    results = list(db.marks.aggregate(pipeline))
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results

def get_subject_averages(semester: int, section: str = None):
    db = get_db()
    pipeline = [
        {"$match": {"semester": semester}},
    ]
    if section:
        pipeline += [
            {"$lookup": {"from": "students","localField": "student_id","foreignField": "student_id","as": "student"}},
            {"$unwind": "$student"},
            {"$match": {"student.section": section}},
        ]
    pipeline += [
        {"$group": {
            "_id": "$subject_code",
            "avg_marks": {"$avg": "$marks_obtained"},
            "max_marks": {"$first": "$max_marks"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}}
    ]
    results = list(db.marks.aggregate(pipeline))
    subjects = {s["code"]: s["name"] for s in db.subjects.find({}, {"_id": 0})}
    for r in results:
        r["subject_name"] = subjects.get(r["_id"], r["_id"])
        r["avg_percentage"] = round((r["avg_marks"] / r["max_marks"]) * 100, 2)
    return results

def get_admin_overview():
    db = get_db()
    total_students = db.students.count_documents({})
    total_teachers = db.teachers.count_documents({})
    total_marks    = db.marks.count_documents({})

    section_counts = {}
    for sec in ["A", "B", "C", "D"]:
        section_counts[sec] = db.students.count_documents({"section": sec})

    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_marks": total_marks,
        "section_counts": section_counts,
    }

# ──────────────────────────────────────────────
#  SEED DATA
# ──────────────────────────────────────────────
def seed_database():
    db = get_db()
    if db.admins.count_documents({}) > 0:
        return  # Already seeded

    print("🌱 Seeding database...")

    # Admin
    db.admins.insert_one({
        "name": "Dr. Admin",
        "username": "admin",
        "password": hash_password("admin123"),
        "email": "admin@mca.edu",
        "created_at": datetime.utcnow()
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
                "max_marks": 100
            })
            sub_id += 1
    db.subjects.insert_many(subjects_to_insert)

    # Students  (4 sections × 10 = 40)
    sections = ["A", "B", "C", "D"]
    first_names = [
        "Aarav","Bhavya","Chirag","Deepika","Eshan",
        "Farhan","Garima","Harsh","Ishaan","Jaya",
        "Kiran","Lata","Mohan","Neha","Om",
        "Pooja","Qasim","Riya","Suresh","Tanya",
        "Uday","Vani","Wasim","Xena","Yash",
        "Zara","Anil","Beena","Chandan","Divya",
        "Ekta","Firoz","Geeta","Hemant","Isha",
        "Jagdish","Kamla","Lokesh","Meera","Nitin"
    ]
    last_names = ["Sharma","Verma","Gupta","Singh","Patel","Mehta","Kumar","Joshi","Rao","Nair"]

    random.seed(42)
    students_to_insert = []
    marks_to_insert    = []
    roll = 1001
    idx  = 0

    for sec in sections:
        for i in range(10):
            fname  = first_names[idx % len(first_names)]
            lname  = random.choice(last_names)
            stu_id = f"STU{roll}"
            uname  = f"{fname.lower()}{roll}"
            students_to_insert.append({
                "student_id":  stu_id,
                "name":        f"{fname} {lname}",
                "username":    uname,
                "password":    hash_password(f"pass{roll}"),
                "roll_number": str(roll),
                "section":     sec,
                "year":        1,
                "semester":    1,
                "email":       f"{uname}@mca.edu",
                "created_at":  datetime.utcnow()
            })
            # Generate marks for all semesters/subjects
            for sub in subjects_to_insert:
                marks_to_insert.append({
                    "student_id":    stu_id,
                    "subject_code":  sub["code"],
                    "semester":      sub["semester"],
                    "marks_obtained": round(random.uniform(45, 98), 1),
                    "max_marks":     100,
                    "updated_at":    datetime.utcnow()
                })
            roll += 1
            idx  += 1

    db.students.insert_many(students_to_insert)
    db.marks.insert_many(marks_to_insert)

    # Teachers (one per subject, section A default)
    teacher_data = [
        ("Prof. Anand Kumar",   "t_anand",   "DS101", "A"),
        ("Prof. Bhavna Shah",   "t_bhavna",  "DB101", "B"),
        ("Prof. Chetan Roy",    "t_chetan",  "CN101", "C"),
        ("Prof. Divya Menon",   "t_divya",   "OS201", "D"),
        ("Prof. Esha Tiwari",   "t_esha",    "SE202", "A"),
        ("Prof. Farida Malik",  "t_farida",  "WT203", "B"),
        ("Prof. Ganesh Iyer",   "t_ganesh",  "ML301", "C"),
        ("Prof. Hina Qureshi",  "t_hina",    "CC302", "D"),
        ("Prof. Inder Kapoor",  "t_inder",   "CY303", "A"),
        ("Prof. Jaya Pillai",   "t_jaya",    "BD401", "B"),
        ("Prof. Karan Joshi",   "t_karan",   "PR402", "C"),
        ("Prof. Lata Saxena",   "t_lata",    "AA403", "D"),
    ]
    teachers_to_insert = []
    for t_idx, (name, uname, subcode, sec) in enumerate(teacher_data):
        teachers_to_insert.append({
            "teacher_id":   f"TCH{t_idx+1:03d}",
            "name":         name,
            "username":     uname,
            "password":     hash_password(f"tpass{t_idx+1}"),
            "subject_code": subcode,
            "section":      sec,
            "email":        f"{uname}@mca.edu",
            "created_at":   datetime.utcnow()
        })
    db.teachers.insert_many(teachers_to_insert)

    # Indexes
    db.students.create_index("username",    unique=True)
    db.students.create_index("roll_number", unique=True)
    db.teachers.create_index("username",    unique=True)
    db.marks.create_index([("student_id", 1), ("subject_code", 1), ("semester", 1)], unique=True)

    print("✅ Seeding complete.")
