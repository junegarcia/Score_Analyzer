"""Teacher – Dashboard overview."""
import streamlit as st
from components.ui import metric_card, section_header
from components.charts import bar_subject_averages
from utils.database import (
    get_marks_by_subject_section, get_subject_averages,
    get_students_by_section, get_db
)


def render():
    user    = st.session_state.user_data
    t_name  = user.get("name", "Teacher")
    sub_code= user.get("subject_code", "")
    section = user.get("section", "A")

    # Get subject name
    db = get_db()
    sub_doc = db.subjects.find_one({"code": sub_code}, {"_id": 0})
    sub_name = sub_doc["name"] if sub_doc else sub_code
    sem      = sub_doc["semester"] if sub_doc else 1

    st.markdown(f'<div class="page-title">👩‍🏫 {t_name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">Subject: <b>{sub_name}</b> · Section: <b>{section}</b> · Semester: <b>{sem}</b></div>',
                unsafe_allow_html=True)

    # KPIs
    marks = get_marks_by_subject_section(sub_code, section, sem)
    students = get_students_by_section(section)

    total_students = len(students)
    entered_marks  = len(marks)
    avg_marks = round(sum(m["marks_obtained"] for m in marks)/len(marks), 2) if marks else 0
    topper = max(marks, key=lambda x: x["marks_obtained"]) if marks else None

    col1, col2, col3, col4 = st.columns(4)
    with col1: metric_card("Section Students", total_students, f"Section {section}")
    with col2: metric_card("Marks Entered",    entered_marks,  f"of {total_students}", "green" if entered_marks==total_students else "orange")
    with col3: metric_card("Class Average",    f"{avg_marks:.1f}", f"/{100}", "green" if avg_marks>=75 else "orange")
    with col4: metric_card("Topper",           topper["student_name"] if topper else "—", f"{topper['marks_obtained']:.0f}/100" if topper else "", "green")

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick mark status
    section_header("📋", "Mark Entry Status", f"{sub_name} – Section {section}")
    entered_ids = {m["student_id"] for m in marks}
    for stu in students:
        sid = stu["student_id"]
        m = next((x for x in marks if x["student_id"]==sid), None)
        status = f"✅ {m['marks_obtained']:.0f}/100" if m else "⏳ Pending"
        st.markdown(f"**{stu['name']}** ({stu['roll_number']}) — {status}")
