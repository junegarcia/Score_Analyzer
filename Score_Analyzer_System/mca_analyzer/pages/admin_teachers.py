"""Admin – Add / Update / Delete / Assign teachers."""
import streamlit as st
import pandas as pd
import uuid
from components.ui import section_header
from utils.database import (
    get_all_teachers, add_teacher, update_teacher,
    delete_teacher, assign_subject_to_teacher, get_all_subjects
)


def render():
    st.markdown('<div class="page-title">👩‍🏫 Teacher Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage faculty and subject assignments</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Add Teacher", "✏️ Edit / Delete", "🔗 Assign Subject"])

    # ── VIEW ALL ─────────────────────────────────────────────
    with tab1:
        section_header("📋", "All Teachers")
        teachers = get_all_teachers()
        subjects = {s["code"]: s["name"] for s in get_all_subjects()}

        if teachers:
            rows = [{
                "Teacher ID":  t.get("teacher_id",""),
                "Name":        t.get("name",""),
                "Username":    t.get("username",""),
                "Subject":     subjects.get(t.get("subject_code",""), t.get("subject_code","—")),
                "Section":     t.get("section","—"),
                "Email":       t.get("email",""),
            } for t in teachers]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(f"{len(teachers)} teacher(s) registered")
        else:
            st.info("No teachers found.")

    # ── ADD TEACHER ───────────────────────────────────────────
    with tab2:
        section_header("➕", "Add New Teacher")

        subjects_list = get_all_subjects()
        sub_options   = {f"{s['name']} (Sem {s['semester']})": s["code"] for s in subjects_list}

        with st.form("add_teacher_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name     = st.text_input("Full Name *")
                username = st.text_input("Username *")
                password = st.text_input("Password *", type="password")
                email    = st.text_input("Email")
            with c2:
                sub_label = st.selectbox("Assign Subject *", list(sub_options.keys()))
                section   = st.selectbox("Assign Section *", ["A","B","C","D"])

            submitted = st.form_submit_button("➕ Add Teacher", type="primary", use_container_width=True)
            if submitted:
                if not all([name, username, password]):
                    st.error("Please fill all required (*) fields.")
                else:
                    ok, msg = add_teacher({
                        "teacher_id":   f"TCH{uuid.uuid4().hex[:6].upper()}",
                        "name":         name.strip(),
                        "username":     username.strip(),
                        "password":     password,
                        "subject_code": sub_options[sub_label],
                        "section":      section,
                        "email":        email.strip(),
                    })
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

    # ── EDIT / DELETE ─────────────────────────────────────────
    with tab3:
        section_header("✏️", "Edit or Delete Teacher")

        teachers_all = get_all_teachers()
        if not teachers_all:
            st.info("No teachers in the system.")
        else:
            t_map  = {f"{t['name']} ({t.get('username','')})": t for t in teachers_all}
            choice = st.selectbox("Select Teacher", list(t_map.keys()), key="edit_teacher_sel")
            t      = t_map[choice]

            with st.form("edit_teacher_form"):
                c1, c2 = st.columns(2)
                with c1:
                    new_name  = st.text_input("Full Name", value=t.get("name",""))
                    new_uname = st.text_input("Username",  value=t.get("username",""))
                    new_pwd   = st.text_input("New Password (blank = keep)", type="password")
                    new_email = st.text_input("Email",     value=t.get("email",""))
                with c2:
                    subjects_list2 = get_all_subjects()
                    sub_opts2 = {f"{s['name']} (Sem {s['semester']})": s["code"] for s in subjects_list2}
                    codes = list(sub_opts2.values())
                    cur_idx = codes.index(t.get("subject_code","")) if t.get("subject_code") in codes else 0
                    new_sub_label = st.selectbox("Subject", list(sub_opts2.keys()), index=cur_idx)
                    new_section   = st.selectbox("Section", ["A","B","C","D"],
                                                  index=["A","B","C","D"].index(t.get("section","A")))

                col_s, col_d = st.columns(2)
                with col_s:
                    save   = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
                with col_d:
                    delete = st.form_submit_button("🗑️ Delete", use_container_width=True)

                if save:
                    updates = {
                        "name": new_name, "username": new_uname,
                        "subject_code": sub_opts2[new_sub_label],
                        "section": new_section, "email": new_email,
                    }
                    if new_pwd:
                        updates["password"] = new_pwd
                    ok, msg = update_teacher(t["teacher_id"], updates)
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

                if delete:
                    ok, msg = delete_teacher(t["teacher_id"])
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
                    if ok:
                        st.rerun()

    # ── ASSIGN SUBJECT ────────────────────────────────────────
    with tab4:
        section_header("🔗", "Assign Subject & Section to Teacher")

        teachers_all2 = get_all_teachers()
        if not teachers_all2:
            st.info("No teachers available.")
        else:
            t_map2  = {f"{t['name']}": t for t in teachers_all2}
            t_choice= st.selectbox("Teacher", list(t_map2.keys()), key="assign_t")
            t2      = t_map2[t_choice]

            subjects_list3 = get_all_subjects()
            sub_opts3 = {f"{s['name']} (Sem {s['semester']})": s["code"] for s in subjects_list3}
            codes3 = list(sub_opts3.values())
            cur_idx3 = codes3.index(t2.get("subject_code","")) if t2.get("subject_code") in codes3 else 0

            new_sub3 = st.selectbox("Subject", list(sub_opts3.keys()), index=cur_idx3, key="assign_sub")
            new_sec3 = st.selectbox("Section", ["A","B","C","D"],
                                     index=["A","B","C","D"].index(t2.get("section","A")), key="assign_sec")

            if st.button("🔗 Assign", type="primary"):
                ok, msg = assign_subject_to_teacher(t2["teacher_id"], sub_opts3[new_sub3], new_sec3)
                st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
