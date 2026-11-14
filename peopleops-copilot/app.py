import os
import sys
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

st.set_page_config(
    page_title="PeopleOps Copilot",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 PeopleOps Copilot")
st.caption("Autonomous HR Policy, Leave & Expense Reimbursement Assistant")

# Sidebar with Quick Demo Prompts & Employee Context
with st.sidebar:
    st.header("🏢 Employee Context")
    active_emp = st.selectbox(
        "Select Active Employee ID",
        ["EMP-101 (Jahedul Islam)", "EMP-102 (Rahim Uddin)", "EMP-105 (Employee 105)"],
    )
    emp_id = active_emp.split(" ")[0]
    st.info(f"Active Session ID: **{emp_id}**")

    st.divider()
    st.subheader("⚡ Quick Test Prompts")
    sample_prompts = [
        f"Check profile and leave balances for {emp_id}.",
        "How many annual leave days am I entitled to and can unused days be carried forward?",
        f"Apply for 2 days of Casual leave for {emp_id} due to personal urgent work.",
        f"Apply for 5 days of Annual leave for {emp_id} for a family vacation.",
        f"Submit an expense claim of 1,500 BDT for {emp_id} under Internet for monthly broadband.",
        f"Submit an expense claim of 7,500 BDT for {emp_id} under Client Meals for team dinner.",
        f"Show leave and expense history for {emp_id}.",
    ]
    for prompt in sample_prompts:
        if st.button(prompt, use_container_width=True):
            st.session_state["prefill_prompt"] = prompt

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am **PeopleOps Copilot**. Ask me about company HR policies, check your leave balances, apply for leave, or submit expense reimbursement claims.",
        }
    ]

# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle Input (either from sidebar button or chat box)
user_input = st.chat_input("Ask an HR policy question or request leave/expense action...")
if "prefill_prompt" in st.session_state:
    user_input = st.session_state.pop("prefill_prompt")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Consulting HR policies & database..."):
            try:
                reply = run_copilot(user_input)
            except Exception as e:
                reply = f"⚠️ Error processing request: {str(e)}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})