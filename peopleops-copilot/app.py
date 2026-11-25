import os
import sys
import html
import streamlit as st

# Ensure working directory and sys.path are set to this directory (peopleops-copilot)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load Streamlit Cloud Secrets into environment variables if available
try:
    for key, val in st.secrets.items():
        if key not in os.environ:
            os.environ[key] = str(val)
except Exception:
    pass

from src.agent import run_copilot
from src.llm import get_secret, configure_langsmith
from src.tools.hr_tools import (
    get_all_employee_options,
    get_employee_summary,
    get_admin_metrics,
    get_all_leave_requests,
    get_all_expense_claims,
    review_leave_request,
    review_expense_claim,
    get_employee_notifications,
    get_unread_notification_count,
    mark_notification_read,
    mark_all_notifications_read,
)
from data.seed_db import seed_database

st.set_page_config(
    page_title="PeopleOps Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------------------
# Modern Enterprise SaaS Styling (Plus Jakarta Sans + Crisp Cards & Badges)
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }
        .block-container {
            padding-top: 3.3rem !important;
            padding-bottom: 2rem !important;
            max-width: 1220px;
        }
        /* Top Header bar subtle border */
        header[data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.92) !important;
            backdrop-filter: blur(12px);
            border-bottom: 1px solid #E2E8F0;
        }
        /* Sidebar polish */
        section[data-testid="stSidebar"] {
            background: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem !important;
        }
        .brand-card {
            background: linear-gradient(135deg, #4F46E5 0%, #6366F1 55%, #0EA5E9 100%);
            color: #FFFFFF;
            border-radius: 14px;
            padding: 0.95rem 1.05rem;
            margin-bottom: 0.85rem;
            box-shadow: 0 8px 20px rgba(79, 70, 229, 0.22);
        }
        .brand-card h3 {
            margin: 0;
            font-size: 1.15rem;
            font-weight: 800;
            color: #FFFFFF !important;
            letter-spacing: -0.02em;
        }
        .brand-card p {
            margin: 0.2rem 0 0 0;
            font-size: 0.76rem;
            color: rgba(255, 255, 255, 0.88) !important;
        }
        .status-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-bottom: 0.5rem;
        }
        .sys-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
        }
        .chip-green {
            background: #ECFDF5;
            color: #047857;
            border: 1px solid #A7F3D0;
        }
        .chip-amber {
            background: #FFFBEB;
            color: #B45309;
            border: 1px solid #FDE68A;
        }
        /* Employee Profile Hero Strip */
        .emp-hero {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .emp-identity {
            display: flex;
            align-items: center;
            gap: 0.9rem;
        }
        .emp-avatar {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            background: linear-gradient(135deg, #4F46E5, #0EA5E9);
            color: #FFFFFF;
            font-weight: 800;
            font-size: 1.05rem;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
        }
        .emp-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: #0F172A;
            margin: 0;
            line-height: 1.25;
        }
        .emp-meta {
            font-size: 0.80rem;
            color: #64748B;
            margin: 0.15rem 0 0 0;
        }
        .leave-grid {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }
        .leave-tile {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 0.55rem 0.85rem;
            min-width: 126px;
        }
        .leave-tile-top {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            font-size: 0.74rem;
            color: #64748B;
            font-weight: 600;
        }
        .leave-tile-val {
            font-size: 1.05rem;
            font-weight: 800;
            color: #0F172A;
            margin: 0.15rem 0 0.3rem 0;
        }
        .progress-track {
            width: 100%;
            height: 6px;
            background: #E2E8F0;
            border-radius: 999px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            border-radius: 999px;
        }
        /* Admin Banner & KPI Cards */
        .admin-banner {
            background: linear-gradient(135deg, #1E1B4B 0%, #312E81 55%, #4338CA 100%);
            color: #FFFFFF;
            border-radius: 16px;
            padding: 1.15rem 1.4rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 24px rgba(49, 46, 129, 0.18);
        }
        .admin-banner h2 {
            margin: 0;
            font-size: 1.35rem;
            font-weight: 800;
            color: #FFFFFF !important;
            letter-spacing: -0.02em;
        }
        .admin-banner p {
            margin: 0.25rem 0 0 0;
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.84) !important;
        }
        .kpi-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 0.95rem 1.1rem;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
            border-top: 3px solid #4F46E5;
        }
        .kpi-amber { border-top-color: #F59E0B; }
        .kpi-rose  { border-top-color: #EF4444; }
        .kpi-green { border-top-color: #10B981; }
        .kpi-label {
            font-size: 0.76rem;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .kpi-value {
            font-size: 1.65rem;
            font-weight: 800;
            color: #0F172A;
            margin: 0.2rem 0 0.1rem 0;
            line-height: 1.15;
        }
        .kpi-sub {
            font-size: 0.76rem;
            color: #64748B;
            font-weight: 500;
        }
        /* Status Pills */
        .status-pill {
            display: inline-block;
            padding: 0.20rem 0.62rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            margin-right: 0.35rem;
            letter-spacing: 0.02em;
        }
        .pill-pending {
            background: #FEF3C7;
            color: #B45309;
            border: 1px solid #FDE68A;
        }
        .pill-approved {
            background: #D1FAE5;
            color: #047857;
            border: 1px solid #A7F3D0;
        }
        .pill-declined {
            background: #FEE2E2;
            color: #B91C1C;
            border: 1px solid #FECACA;
        }
        .pill-info {
            background: #E0E7FF;
            color: #3730A3;
            border: 1px solid #C7D2FE;
        }
        .pill-unread {
            background: #EDE9FE;
            color: #6D28D9;
            border: 1px solid #DDD6FE;
        }
        /* Notification & Escalation Card Polish */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        }
        /* Chat Message Polish */
        div[data-testid="stChatMessage"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 0.85rem 1.05rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03);
        }
        /* Button Polish */
        .stButton > button {
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 0.84rem !important;
            transition: all 0.16s ease !important;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.14);
        }
        section[data-testid="stSidebar"] .stButton > button {
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 0.45rem 0.75rem !important;
            font-size: 0.80rem !important;
            border: 1px solid #E2E8F0 !important;
            background: #F8FAFC !important;
            color: #1E293B !important;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            border-color: #6366F1 !important;
            background: #EEF2FF !important;
            color: #3730A3 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def _initials(name: str) -> str:
    parts = [p for p in name.strip().split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "HR"


# ------------------------------------------------------------------------------
# Sidebar: Brand Card, Compact Status Chips, Searchable 1,470 Employees, Prompts
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-card">
            <h3>🤖 PeopleOps Copilot</h3>
            <p>AI HR Policy RAG • Leave &amp; Expense Automation</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    detected_gemini_key = get_secret("GOOGLE_API_KEY") or get_secret("GEMINI_API_KEY")
    detected_openrouter_key = get_secret("OPENROUTER_API_KEY")
    langsmith_on = configure_langsmith()

    llm_chip = (
        '<span class="sys-chip chip-green">⚡ LLM Ready</span>'
        if (detected_openrouter_key or detected_gemini_key)
        else '<span class="sys-chip chip-amber">🔴 LLM Key Missing</span>'
    )
    ls_chip = (
        '<span class="sys-chip chip-green">📊 LangSmith ON</span>'
        if langsmith_on
        else '<span class="sys-chip chip-amber">📊 LangSmith OFF</span>'
    )
    st.markdown(f'<div class="status-row">{llm_chip}{ls_chip}</div>', unsafe_allow_html=True)

    if not (detected_openrouter_key or detected_gemini_key):
        manual_key = st.text_input(
            "Enter Google API Key:",
            type="password",
            placeholder="Paste API key...",
            key="manual_gemini_key",
        )
        if manual_key:
            os.environ["GOOGLE_API_KEY"] = manual_key.strip()
            st.rerun()

    st.divider()

    @st.cache_data(ttl=60)
    def _load_employees():
        return get_all_employee_options()

    employee_options = _load_employees()
    st.markdown(f"**🏢 Active Employee** `{len(employee_options):,}`")
    active_emp = st.selectbox(
        "Active Employee",
        employee_options,
        label_visibility="collapsed",
        help="Type any Employee ID (e.g. EMP-500) or name to search all 1,470 employees.",
    )
    emp_id = active_emp.split(" ")[0]

    st.divider()
    st.markdown("**⚡ Quick Demo Prompts**")
    sample_prompts = [
        ("📄 Annual Leave Policy (RAG)", "How many annual leave days am I entitled to and can unused days be carried forward?"),
        ("👤 Profile & Leave Balances", f"Check profile and leave balances for {emp_id}."),
        ("✅ Casual Leave — 2d (Auto)", f"Apply for 2 days of Casual leave for {emp_id} due to personal urgent work."),
        ("🚨 Annual Leave — 5d (Risky)", f"Apply for 5 days of Annual leave for {emp_id} for a family vacation."),
        ("✅ Internet Claim — 1,500 BDT", f"Submit an expense claim of 1,500 BDT for {emp_id} under Internet for monthly broadband."),
        ("🚨 Client Meals — 7,500 BDT", f"Submit an expense claim of 7,500 BDT for {emp_id} under Client Meals for team dinner."),
        ("📜 Leave & Expense History", f"Show leave and expense history for {emp_id}."),
    ]
    clicked_prompt = None
    for label, prompt_text in sample_prompts:
        if st.button(label, use_container_width=True):
            clicked_prompt = prompt_text

    st.divider()
    with st.expander("🛠️ Demo Controls", expanded=False):
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        if st.button("🔄 Reset Demo Database", use_container_width=True):
            seed_database()
            st.cache_data.clear()
            st.toast("Database reset to clean demo state (1,470 employees)!", icon="🔄")
            st.rerun()

# ------------------------------------------------------------------------------
# Live Counts for Fixed Top Header Navbar Badges
# ------------------------------------------------------------------------------
metrics = get_admin_metrics()
unread_count = get_unread_notification_count(emp_id)


# ==============================================================================
# PAGE 1: USER COPILOT
# ==============================================================================
def render_copilot():
    emp_summary = get_employee_summary(emp_id)
    if emp_summary:
        ann_pct = min(100, int((emp_summary["annual_leave"] / 15) * 100))
        cas_pct = min(100, int((emp_summary["casual_leave"] / 10) * 100))
        sck_pct = min(100, int((emp_summary["sick_leave"] / 14) * 100))
        safe_name = html.escape(emp_summary["name"])
        safe_role = html.escape(emp_summary["job_role"])
        safe_dept = html.escape(emp_summary["department"])

        st.markdown(
            f"""
            <div class="emp-hero">
                <div class="emp-identity">
                    <div class="emp-avatar">{_initials(emp_summary['name'])}</div>
                    <div>
                        <div class="emp-name">
                            {safe_name}
                            <span class="status-pill pill-info" style="margin-left:0.4rem;">{emp_summary['employee_id']}</span>
                        </div>
                        <div class="emp-meta">
                            {safe_role} • {safe_dept} • Level {emp_summary['job_level']} • {emp_summary['monthly_income_bdt']:,.0f} BDT/mo
                        </div>
                    </div>
                </div>
                <div class="leave-grid">
                    <div class="leave-tile">
                        <div class="leave-tile-top"><span>Annual</span><span>/ 15d</span></div>
                        <div class="leave-tile-val">{emp_summary['annual_leave']} days</div>
                        <div class="progress-track"><div class="progress-fill" style="width:{ann_pct}%; background:#4F46E5;"></div></div>
                    </div>
                    <div class="leave-tile">
                        <div class="leave-tile-top"><span>Casual</span><span>/ 10d</span></div>
                        <div class="leave-tile-val">{emp_summary['casual_leave']} days</div>
                        <div class="progress-track"><div class="progress-fill" style="width:{cas_pct}%; background:#10B981;"></div></div>
                    </div>
                    <div class="leave-tile">
                        <div class="leave-tile-top"><span>Sick</span><span>/ 14d</span></div>
                        <div class="leave-tile-val">{emp_summary['sick_leave']} days</div>
                        <div class="progress-track"><div class="progress-fill" style="width:{sck_pct}%; background:#0EA5E9;"></div></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if unread_count > 0:
        b_col1, b_col2 = st.columns([4.2, 1.1], vertical_alignment="center")
        b_col1.info(
            f"🔔 **{emp_id}** has **{unread_count} unread notification(s)** from HR Admin.",
            icon="📬",
        )
        if b_col2.button("View Inbox →", type="primary", use_container_width=True):
            st.switch_page(page_notifications)

    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    f"Hello! I am **PeopleOps Copilot** (currently assisting **{emp_id}**). "
                    "Ask me about HR policies with citations, check your leave balances, apply for leave, "
                    "or submit expense reimbursement claims.\n\n"
                    "- **Auto-Approved:** Leave ≤ 3 days & Expenses ≤ 5,000 BDT (within category caps)\n"
                    "- **High-Risk Escalation:** Leave > 3 days or Expenses > 5,000 BDT are routed to the **Admin Panel**, "
                    "and you'll receive an instant update in **Notifications** once reviewed."
                ),
            }
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask an HR policy question or request leave/expense action...")
    if "prefill_prompt" in st.session_state:
        user_input = st.session_state.pop("prefill_prompt")

    if user_input:
        prior_history = list(st.session_state.messages)
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Consulting HR policies & live database..."):
                try:
                    reply = run_copilot(
                        user_input,
                        chat_history=prior_history,
                        active_employee_id=emp_id,
                    )
                except Exception as e:
                    reply = f"⚠️ Error processing request: {str(e)}"
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


# ==============================================================================
# PAGE 2: EMPLOYEE NOTIFICATIONS CENTER
# ==============================================================================
def render_notifications():
    emp_summary = get_employee_summary(emp_id)
    emp_name = emp_summary["name"] if emp_summary else emp_id

    h_left, h_right = st.columns([3.5, 1.2], vertical_alignment="center")
    with h_left:
        st.markdown(f"### 🔔 Notification Inbox — {emp_name} (`{emp_id}`)")
        st.caption("Real-time approval & decline decisions delivered directly from HR Admin.")
    with h_right:
        if unread_count > 0:
            if st.button("✅ Mark All Read", type="primary", use_container_width=True):
                mark_all_notifications_read(emp_id)
                st.toast("All notifications marked as read!", icon="✅")
                st.rerun()

    notifs = get_employee_notifications(emp_id)
    if not notifs:
        st.info(
            f"No notifications yet for **{emp_name} ({emp_id})**. "
            "When HR Admin approves or declines a High-Risk request, it will appear right here."
        )
    else:
        for n in notifs:
            pill_cls = (
                "pill-approved"
                if n["notif_type"] == "approved"
                else "pill-declined"
                if n["notif_type"] == "declined"
                else "pill-info"
            )
            status_word = (
                "APPROVED"
                if n["notif_type"] == "approved"
                else "DECLINED"
                if n["notif_type"] == "declined"
                else "UPDATE"
            )
            unread_pill = "<span class='status-pill pill-unread'>NEW</span>" if not n["is_read"] else ""

            with st.container(border=True):
                c_left, c_right = st.columns([4.2, 1], vertical_alignment="center")
                with c_left:
                    st.markdown(
                        f"{unread_pill}<span class='status-pill {pill_cls}'>{status_word}</span> "
                        f"**{n['title']}**",
                        unsafe_allow_html=True,
                    )
                    st.markdown(n["message"])
                    st.caption(f"🕒 {n['created_at']}  •  Reference ID: `{n['related_id'] or 'N/A'}`")
                with c_right:
                    if not n["is_read"]:
                        if st.button("Mark Read", key=f"read_{n['notification_id']}", use_container_width=True):
                            mark_notification_read(n["notification_id"])
                            st.rerun()
                    else:
                        st.markdown("<div style='text-align:center;color:#94A3B8;font-size:0.82rem;font-weight:600;'>✓ Read</div>", unsafe_allow_html=True)


# ==============================================================================
# PAGE 3: ADMIN PANEL (HUMAN-IN-THE-LOOP GOVERNANCE CONSOLE)
# ==============================================================================
def render_admin():
    st.markdown(
        """
        <div class="admin-banner">
            <h2>🛡️ HR Admin Governance Console</h2>
            <p>Review High-Risk escalations (&gt;3 days leave or &gt;5,000 BDT / over-cap expenses) with instant employee notifications &amp; audit logging.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Styled KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">👥 Total Workforce</div>
            <div class="kpi-value">{metrics['total_employees']:,}</div>
            <div class="kpi-sub">Active HR Database Records</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    k2.markdown(
        f"""
        <div class="kpi-card kpi-amber">
            <div class="kpi-label">🗓️ Pending Leaves</div>
            <div class="kpi-value">{metrics['pending_leaves']}</div>
            <div class="kpi-sub">{'Action required (>3 days)' if metrics['pending_leaves'] > 0 else 'Queue completely clear'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    k3.markdown(
        f"""
        <div class="kpi-card kpi-rose">
            <div class="kpi-label">💳 Pending Expenses</div>
            <div class="kpi-value">{metrics['pending_expenses']}</div>
            <div class="kpi-sub">{metrics['pending_expense_bdt']:,.0f} BDT awaiting approval</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    k4.markdown(
        f"""
        <div class="kpi-card kpi-green">
            <div class="kpi-label">✅ Processed Total</div>
            <div class="kpi-value">{metrics['total_processed']}</div>
            <div class="kpi-sub">Approved &amp; Declined Audit Trail</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🚨 High-Risk Escalation Queue")

    pending_leaves = get_all_leave_requests(pending_only=True)
    pending_expenses = get_all_expense_claims(pending_only=True)

    col_leaves, col_expenses = st.columns(2, gap="large")

    with col_leaves:
        st.markdown(f"**🗓️ Pending Leave Requests ({len(pending_leaves)})**")
        if not pending_leaves:
            st.success("All high-risk leave requests have been reviewed.")
        else:
            for lv in pending_leaves:
                with st.container(border=True):
                    top_l, top_r = st.columns([2.2, 1])
                    top_l.markdown(f"**{lv['employee_name']}** (`{lv['employee_id']}`)")
                    top_r.markdown(
                        f"<div style='text-align:right'><span class='status-pill pill-pending'>{lv['leave_type']} • {lv['days']}d</span></div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        f"ID: `{lv['leave_id']}`  •  {lv['department']}  •  Available Balance: **{lv['available_balance']} days**"
                    )
                    st.markdown(f"**Reason:** {lv['reason']}")
                    st.warning(f"{lv['status']}", icon="🛡️")

                    note = st.text_input(
                        "Manager Remark (sent to employee)",
                        key=f"lv_note_{lv['leave_id']}",
                        placeholder="e.g., Approved for Q4 schedule / Declined due to sprint deadline",
                    )
                    b1, b2 = st.columns(2)
                    if b1.button("✅ Approve Leave", key=f"lv_app_{lv['leave_id']}", type="primary", use_container_width=True):
                        ok, msg = review_leave_request(lv["leave_id"], "approve", note)
                        if ok:
                            st.toast(f"{msg} — Notified {lv['employee_id']}!", icon="🔔")
                            st.rerun()
                        else:
                            st.error(msg)
                    if b2.button("❌ Decline Leave", key=f"lv_dec_{lv['leave_id']}", use_container_width=True):
                        ok, msg = review_leave_request(lv["leave_id"], "decline", note)
                        if ok:
                            st.toast(f"{msg} — Notified {lv['employee_id']}!", icon="🔔")
                            st.rerun()
                        else:
                            st.error(msg)

    with col_expenses:
        st.markdown(f"**💳 Pending Expense Claims ({len(pending_expenses)})**")
        if not pending_expenses:
            st.success("All high-risk expense claims have been reviewed.")
        else:
            for clm in pending_expenses:
                with st.container(border=True):
                    top_l, top_r = st.columns([2.2, 1])
                    top_l.markdown(f"**{clm['employee_name']}** (`{clm['employee_id']}`)")
                    top_r.markdown(
                        f"<div style='text-align:right'><span class='status-pill pill-declined'>{clm['amount_bdt']:,.0f} BDT</span></div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"ID: `{clm['claim_id']}`  •  {clm['department']}  •  Category: **{clm['category']}**")
                    st.markdown(f"**Description:** {clm['description']}")
                    st.warning(f"{clm['status']}", icon="🛡️")

                    note = st.text_input(
                        "Manager Remark (sent to employee)",
                        key=f"clm_note_{clm['claim_id']}",
                        placeholder="e.g., Verified receipt / Exceeds quarterly budget",
                    )
                    b1, b2 = st.columns(2)
                    if b1.button("✅ Approve Claim", key=f"clm_app_{clm['claim_id']}", type="primary", use_container_width=True):
                        ok, msg = review_expense_claim(clm["claim_id"], "approve", note)
                        if ok:
                            st.toast(f"{msg} — Notified {clm['employee_id']}!", icon="🔔")
                            st.rerun()
                        else:
                            st.error(msg)
                    if b2.button("❌ Decline Claim", key=f"clm_dec_{clm['claim_id']}", use_container_width=True):
                        ok, msg = review_expense_claim(clm["claim_id"], "decline", note)
                        if ok:
                            st.toast(f"{msg} — Notified {clm['employee_id']}!", icon="🔔")
                            st.rerun()
                        else:
                            st.error(msg)

    st.markdown("---")
    st.markdown("### 📋 Complete Audit Log & Decision History")
    filter_opt = st.radio(
        "Filter by Status",
        ["All", "Pending", "Approved", "Declined"],
        horizontal=True,
        label_visibility="collapsed",
    )

    def _matches_filter(status_str: str) -> bool:
        if filter_opt == "All":
            return True
        return status_str.lower().startswith(filter_opt.lower())

    all_leaves = [r for r in get_all_leave_requests(False) if _matches_filter(r["status"])]
    all_expenses = [r for r in get_all_expense_claims(False) if _matches_filter(r["status"])]

    log_tab1, log_tab2 = st.tabs([
        f"🗓️ Leave Records ({len(all_leaves)})",
        f"💳 Expense Claims ({len(all_expenses)})",
    ])
    with log_tab1:
        if all_leaves:
            st.dataframe(
                [
                    {
                        "Leave ID": r["leave_id"],
                        "Employee": f"{r['employee_name']} ({r['employee_id']})",
                        "Dept": r["department"],
                        "Type": r["leave_type"],
                        "Days": r["days"],
                        "Reason": r["reason"],
                        "Status": r["status"],
                    }
                    for r in all_leaves
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No leave records match this filter.")

    with log_tab2:
        if all_expenses:
            st.dataframe(
                [
                    {
                        "Claim ID": r["claim_id"],
                        "Employee": f"{r['employee_name']} ({r['employee_id']})",
                        "Dept": r["department"],
                        "Category": r["category"],
                        "Amount (BDT)": f"{r['amount_bdt']:,.2f}",
                        "Description": r["description"],
                        "Status": r["status"],
                    }
                    for r in all_expenses
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No expense claims match this filter.")


# ------------------------------------------------------------------------------
# Native Fixed Top Header Navigation Bar (Streamlit 1.67 position="top")
# ------------------------------------------------------------------------------
notif_title = f"Notifications ({unread_count})" if unread_count > 0 else "Notifications"
admin_title = f"Admin Panel ({metrics['pending_total']})" if metrics["pending_total"] > 0 else "Admin Panel"

page_copilot = st.Page(render_copilot, title="User Copilot", icon="💬", url_path="copilot", default=True)
page_notifications = st.Page(render_notifications, title=notif_title, icon="🔔", url_path="notifications")
page_admin = st.Page(render_admin, title=admin_title, icon="🛡️", url_path="admin")

nav = st.navigation([page_copilot, page_notifications, page_admin], position="top")

if clicked_prompt:
    st.session_state["prefill_prompt"] = clicked_prompt
    st.switch_page(page_copilot)

nav.run()
