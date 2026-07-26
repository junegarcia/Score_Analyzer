"""
Shared UI components – CSS injection, sidebar, metric cards, etc.
"""
import streamlit as st

# ─────────────────────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Root variables ── */
:root {
    --primary:   #1E3A8A;
    --primary-light: #3B82F6;
    --secondary: #0EA5E9;
    --accent:    #06B6D4;
    --success:   #10B981;
    --warning:   #F59E0B;
    --danger:    #EF4444;
    --bg:        #F0F4FF;
    --card-bg:   #FFFFFF;
    --text:      #1E293B;
    --text-muted:#64748B;
    --border:    #E2E8F0;
    --sidebar-w: 260px;
}

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--text);
}

.stApp { background: var(--bg) !important; }

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem !important; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, var(--primary) 0%, #1e40af 60%, #1d4ed8 100%) !important;
    width: var(--sidebar-w) !important;
}
[data-testid="stSidebar"] * { color: #fff !important; }
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: #fff !important;
    border-radius: 10px !important;
    margin-bottom: 4px;
    font-weight: 500;
    transition: all .2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.25) !important;
    transform: translateX(4px);
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.25) !important; }

/* ── Metric cards ── */
.metric-card {
    background: var(--card-bg);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 2px 12px rgba(30,58,138,.08);
    border-left: 5px solid var(--primary-light);
    transition: transform .2s, box-shadow .2s;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(30,58,138,.14); }
.metric-card .label { font-size: .8rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .06em; }
.metric-card .value { font-size: 2rem; font-weight: 700; color: var(--primary); line-height: 1.1; }
.metric-card .sub   { font-size: .78rem; color: var(--text-muted); margin-top: .25rem; }
.metric-card.green  { border-left-color: var(--success); }
.metric-card.green .value { color: var(--success); }
.metric-card.orange { border-left-color: var(--warning); }
.metric-card.orange .value { color: var(--warning); }
.metric-card.red    { border-left-color: var(--danger); }
.metric-card.red .value { color: var(--danger); }

/* ── Section headers ── */
.section-header {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    color: #fff !important;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: .75rem;
}
.section-header h2 { margin: 0; font-size: 1.25rem; font-weight: 700; color: #fff !important; }
.section-header p  { margin: 0; font-size: .85rem; opacity: .85; color: #fff !important; }

/* ── Page title ── */
.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--primary);
    margin-bottom: .25rem;
}
.page-subtitle { font-size: .95rem; color: var(--text-muted); margin-bottom: 1.5rem; }

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: .2rem .7rem;
    border-radius: 99px;
    font-size: .75rem;
    font-weight: 600;
}
.badge-blue   { background: #DBEAFE; color: #1E40AF; }
.badge-green  { background: #D1FAE5; color: #065F46; }
.badge-orange { background: #FEF3C7; color: #92400E; }
.badge-red    { background: #FEE2E2; color: #991B1B; }
.badge-purple { background: #EDE9FE; color: #5B21B6; }

/* ── Tables ── */
.stDataFrame { border-radius: 12px !important; overflow: hidden; }
.stDataFrame thead th {
    background: var(--primary) !important;
    color: #fff !important;
    font-weight: 600 !important;
}

/* ── Inputs ── */
.stTextInput input, .stSelectbox select, .stNumberInput input {
    border-radius: 10px !important;
    border: 1.5px solid var(--border) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--primary-light) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.15) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all .2s !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; }

/* ── Alerts / info boxes ── */
.info-box {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    font-size: .9rem;
    color: #1E40AF;
}
.success-box {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    font-size: .9rem;
    color: #166534;
}
.warning-box {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    font-size: .9rem;
    color: #92400E;
}

/* ── Login page ── */
.login-container {
    max-width: 440px;
    margin: 3rem auto;
    background: var(--card-bg);
    border-radius: 20px;
    padding: 2.5rem;
    box-shadow: 0 8px 40px rgba(30,58,138,.12);
}
.login-logo {
    text-align: center;
    margin-bottom: 1.5rem;
}
.login-logo .logo-icon {
    width: 72px; height: 72px;
    background: linear-gradient(135deg, var(--primary), var(--primary-light));
    border-radius: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    margin-bottom: .75rem;
}
.login-logo h1 { font-size: 1.5rem; font-weight: 800; color: var(--primary); margin: 0; }
.login-logo p  { font-size: .9rem; color: var(--text-muted); margin: .25rem 0 0; }

/* ── Rank badge ── */
.rank-1 { color: #F59E0B; font-weight: 700; }
.rank-2 { color: #94A3B8; font-weight: 700; }
.rank-3 { color: #CD7F32; font-weight: 700; }

/* ── Progress bar ── */
.prog-wrap { background: #E2E8F0; border-radius: 99px; height: 10px; overflow: hidden; }
.prog-fill  { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--primary), var(--primary-light)); }

/* ── Divider ── */
.styled-hr { border: none; border-top: 2px solid var(--border); margin: 1.5rem 0; }
</style>
"""

def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
def render_sidebar(role: str, name: str):
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:1.5rem 0 1rem;">
            <div style="width:60px;height:60px;background:rgba(255,255,255,.2);
                        border-radius:16px;display:inline-flex;align-items:center;
                        justify-content:center;font-size:1.8rem;margin-bottom:.75rem;">
                {"🎓" if role=="student" else "👩‍🏫" if role=="teacher" else "👩‍💼"}
            </div>
            <div style="font-weight:700;font-size:1rem;">{name}</div>
            <div style="font-size:.75rem;opacity:.8;margin-top:.2rem;
                        background:rgba(255,255,255,.15);border-radius:20px;
                        padding:.15rem .75rem;display:inline-block;">
                {role.upper()}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        nav = []
        if role == "student":
            nav = [
                ("🏠", "Dashboard",      "student_dashboard"),
                ("📊", "My Marks",       "student_marks"),
                ("📈", "Analytics",      "student_analytics"),
                ("🏆", "Semester Rank",  "student_rank"),
            ]
        elif role == "teacher":
            nav = [
                ("🏠", "Dashboard",      "teacher_dashboard"),
                ("📝", "Upload Marks",   "teacher_upload"),
                ("✏️", "Edit Marks",     "teacher_edit"),
                ("📊", "Analytics",      "teacher_analytics"),
                ("🏆", "Performers",     "teacher_performers"),
            ]
        else:  # admin
            nav = [
                ("🏠", "Dashboard",      "admin_dashboard"),
                ("👥", "Students",       "admin_students"),
                ("👩‍🏫", "Teachers",      "admin_teachers"),
                ("📊", "All Marks",      "admin_marks"),
                ("📈", "Analytics",      "admin_analytics"),
            ]

        for icon, label, page_key in nav:
            active = st.session_state.get("page") == page_key
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if active else "secondary"
            ):
                st.session_state.page = page_key
                st.rerun()

        st.markdown("---")
        if st.button("🚪  Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ─────────────────────────────────────────────────────────────
#  METRIC CARD
# ─────────────────────────────────────────────────────────────
def metric_card(label: str, value, sub: str = "", color: str = ""):
    cls = f"metric-card {color}"
    st.markdown(f"""
    <div class="{cls}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def section_header(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size:1.5rem">{icon}</span>
        <div>
            <h2>{title}</h2>
            {"<p>" + subtitle + "</p>" if subtitle else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

def progress_bar(pct: float):
    color = "#10B981" if pct >= 75 else "#F59E0B" if pct >= 50 else "#EF4444"
    st.markdown(f"""
    <div class="prog-wrap">
        <div class="prog-fill" style="width:{pct}%;background:{color};"></div>
    </div>
    <div style="font-size:.78rem;color:#64748B;margin-top:.2rem;">{pct:.1f}%</div>
    """, unsafe_allow_html=True)

def grade_badge(pct: float) -> str:
    if pct >= 90: return '<span class="badge badge-green">A+</span>'
    if pct >= 80: return '<span class="badge badge-blue">A</span>'
    if pct >= 70: return '<span class="badge badge-blue">B</span>'
    if pct >= 60: return '<span class="badge badge-orange">C</span>'
    if pct >= 50: return '<span class="badge badge-orange">D</span>'
    return '<span class="badge badge-red">F</span>'
