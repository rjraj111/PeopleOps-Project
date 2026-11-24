import os
import sqlite3
import uuid
from langchain_core.tools import tool

DB_PATH = os.path.join("data", "db", "hr_system.db")

def _get_connection():
    return sqlite3.connect(DB_PATH)

@tool
def get_employee_profile_and_balances(employee_id: str) -> str:
    """Retrieve an employee's profile details, salary, and current leave balances (Annual, Casual, Sick) by employee_id (e.g., 'EMP-101')."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT employee_id, name, department, job_role, job_level, monthly_income_bdt, annual_leave_balance, casual_leave_balance, sick_leave_balance FROM employees WHERE employee_id = ?",
        (employee_id.strip().upper(),),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return f"Employee ID '{employee_id}' not found in the HR database."

    return (
        f"Employee Profile ({row[0]}):\n"
        f"- Name: {row[1]}\n"
        f"- Department: {row[2]} | Role: {row[3]} (Level {row[4]})\n"
        f"- Monthly Income: {row[5]:,.2f} BDT\n"
        f"- Leave Balances -> Annual: {row[6]} days | Casual: {row[7]} days | Sick: {row[8]} days"
    )

@tool
def submit_leave_request(employee_id: str, leave_type: str, days: int, reason: str) -> str:
    """Submit a leave request for an employee. Checks balance and applies High-Risk Escalation rules (>3 consecutive days requires manager approval)."""
    emp_id = employee_id.strip().upper()
    l_type = leave_type.strip().capitalize()
    valid_types = {"Annual": "annual_leave_balance", "Casual": "casual_leave_balance", "Sick": "sick_leave_balance"}

    if l_type not in valid_types:
        return f"Invalid leave type '{leave_type}'. Must be one of: Annual, Casual, Sick."
    if days <= 0:
        return "Leave days must be greater than 0."

    conn = _get_connection()
    cursor = conn.cursor()
    col_name = valid_types[l_type]
    cursor.execute(f"SELECT name, {col_name} FROM employees WHERE employee_id = ?", (emp_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return f"Employee ID '{emp_id}' not found."

    emp_name, current_balance = row
    if days > current_balance:
        conn.close()
        return f"Insufficient {l_type} leave balance for {emp_name} ({emp_id}). Requested: {days} days, Available: {current_balance} days."

    leave_id = f"LV-{uuid.uuid4().hex[:6].upper()}"
    # Policy Rule (Sec 3): Any single leave request exceeding 3 consecutive days requires manager approval
    if days > 3:
        status = "Pending Manager Approval (High-Risk Escalation: >3 days)"
    else:
        status = "Approved"
        cursor.execute(f"UPDATE employees SET {col_name} = {col_name} - ? WHERE employee_id = ?", (days, emp_id))

    cursor.execute(
        "INSERT INTO leave_records (leave_id, employee_id, leave_type, days, reason, status) VALUES (?, ?, ?, ?, ?, ?)",
        (leave_id, emp_id, l_type, days, reason, status),
    )
    conn.commit()
    conn.close()

    return (
        f"Leave Request Submitted!\n"
        f"- Leave ID: {leave_id}\n"
        f"- Employee: {emp_name} ({emp_id})\n"
        f"- Type & Duration: {l_type} Leave ({days} days)\n"
        f"- Reason: {reason}\n"
        f"- Status: {status}"
    )

@tool
def submit_expense_claim(employee_id: str, category: str, amount_bdt: float, description: str) -> str:
    """Submit an expense reimbursement claim in BDT. Applies category caps and High-Risk Escalation rules (>5,000 BDT requires manager approval)."""
    emp_id = employee_id.strip().upper()
    if amount_bdt <= 0:
        return "Expense amount must be greater than 0 BDT."

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM employees WHERE employee_id = ?", (emp_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return f"Employee ID '{emp_id}' not found."

    emp_name = row[0]
    claim_id = f"CLM-{uuid.uuid4().hex[:6].upper()}"

    # Policy Rule (Sec 3): Claims > 5,000 BDT require explicit human manager approval
    if amount_bdt > 5000:
        status = "Pending Manager Approval (High-Risk Escalation: >5,000 BDT)"
    else:
        status = "Approved"

    cursor.execute(
        "INSERT INTO expense_claims (claim_id, employee_id, category, amount_bdt, description, status) VALUES (?, ?, ?, ?, ?, ?)",
        (claim_id, emp_id, category.strip(), amount_bdt, description.strip(), status),
    )
    conn.commit()
    conn.close()

    return (
        f"Expense Claim Recorded!\n"
        f"- Claim ID: {claim_id}\n"
        f"- Employee: {emp_name} ({emp_id})\n"
        f"- Category: {category} | Amount: {amount_bdt:,.2f} BDT\n"
        f"- Description: {description}\n"
        f"- Status: {status}"
    )

@tool
def get_employee_history(employee_id: str) -> str:
    """Fetch past leave records and expense claims for a given employee_id."""
    emp_id = employee_id.strip().upper()
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT leave_id, leave_type, days, reason, status FROM leave_records WHERE employee_id = ?", (emp_id,))
    leaves = cursor.fetchall()

    cursor.execute("SELECT claim_id, category, amount_bdt, description, status FROM expense_claims WHERE employee_id = ?", (emp_id,))
    claims = cursor.fetchall()
    conn.close()

    leave_str = "\n".join([f"  * {l[0]}: {l[1]} ({l[2]}d) - {l[3]} [{l[4]}]" for l in leaves]) or "  * None"
    claim_str = "\n".join([f"  * {c[0]}: {c[1]} ({c[2]:,.2f} BDT) - {c[3]} [{c[4]}]" for c in claims]) or "  * None"

    return f"History for {emp_id}:\nLeave Records:\n{leave_str}\nExpense Claims:\n{claim_str}"
