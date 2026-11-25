import os
import sqlite3
import uuid
from datetime import datetime
from langchain_core.tools import tool

DB_PATH = os.path.join("data", "db", "hr_system.db")

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            related_id TEXT,
            notif_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn

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
    cat_clean = category.strip()
    cat_lower = cat_clean.lower()

    # Policy Rules (Sec 1 & Sec 3): Category caps + >5,000 BDT High-Risk Escalation
    category_caps = {
        "internet": (2000.0, "Internet & Home Office Utility cap: 2,000 BDT/month"),
        "home office": (2000.0, "Internet & Home Office Utility cap: 2,000 BDT/month"),
        "client meals": (4000.0, "Client Meals & Entertainment cap: 4,000 BDT/meeting"),
        "entertainment": (4000.0, "Client Meals & Entertainment cap: 4,000 BDT/meeting"),
    }

    cap_exceeded_reason = None
    for key, (cap_limit, cap_label) in category_caps.items():
        if key in cat_lower and amount_bdt > cap_limit:
            cap_exceeded_reason = cap_label
            break

    if amount_bdt > 5000:
        status = "Pending Manager Approval (High-Risk Escalation: >5,000 BDT)"
    elif cap_exceeded_reason:
        status = f"Pending Manager Approval (Exceeds Policy Limit — {cap_exceeded_reason})"
    else:
        status = "Approved"

    cursor.execute(
        "INSERT INTO expense_claims (claim_id, employee_id, category, amount_bdt, description, status) VALUES (?, ?, ?, ?, ?, ?)",
        (claim_id, emp_id, cat_clean, amount_bdt, description.strip(), status),
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


# ==============================================================================
# Admin Panel & UI Helper Functions (Human-in-the-Loop Approvals)
# ==============================================================================

def get_all_employee_options() -> list[str]:
    """Return all employees formatted as 'EMP-101 (Jahedul Islam)' ordered by numeric ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT employee_id, name
        FROM employees
        ORDER BY CAST(REPLACE(employee_id, 'EMP-', '') AS INTEGER) ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [f"{r[0]} ({r[1]})" for r in rows]


def get_employee_summary(employee_id: str) -> dict | None:
    """Return structured employee profile & leave balances for UI display."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT employee_id, name, department, job_role, job_level,
               monthly_income_bdt, annual_leave_balance, casual_leave_balance, sick_leave_balance
        FROM employees WHERE employee_id = ?
        """,
        (employee_id.strip().upper(),),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "employee_id": row[0],
        "name": row[1],
        "department": row[2],
        "job_role": row[3],
        "job_level": row[4],
        "monthly_income_bdt": row[5],
        "annual_leave": row[6],
        "casual_leave": row[7],
        "sick_leave": row[8],
    }


def get_admin_metrics() -> dict:
    """Return high-level HR & approval metrics for the Admin Dashboard."""
    conn = _get_connection()
    cursor = conn.cursor()
    total_employees = cursor.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    pending_leaves = cursor.execute(
        "SELECT COUNT(*) FROM leave_records WHERE status LIKE 'Pending%'"
    ).fetchone()[0]
    pending_expenses = cursor.execute(
        "SELECT COUNT(*) FROM expense_claims WHERE status LIKE 'Pending%'"
    ).fetchone()[0]
    pending_expense_bdt = cursor.execute(
        "SELECT COALESCE(SUM(amount_bdt), 0) FROM expense_claims WHERE status LIKE 'Pending%'"
    ).fetchone()[0]
    total_processed = cursor.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM leave_records WHERE status NOT LIKE 'Pending%') +
            (SELECT COUNT(*) FROM expense_claims WHERE status NOT LIKE 'Pending%')
        """
    ).fetchone()[0]
    conn.close()
    return {
        "total_employees": total_employees,
        "pending_leaves": pending_leaves,
        "pending_expenses": pending_expenses,
        "pending_total": pending_leaves + pending_expenses,
        "pending_expense_bdt": float(pending_expense_bdt),
        "total_processed": total_processed,
    }


def get_all_leave_requests(pending_only: bool = False) -> list[dict]:
    """Fetch leave records joined with employee details."""
    conn = _get_connection()
    cursor = conn.cursor()
    where_clause = "WHERE l.status LIKE 'Pending%'" if pending_only else ""
    cursor.execute(
        f"""
        SELECT l.leave_id, l.employee_id, e.name, e.department, l.leave_type,
               l.days, l.reason, l.status,
               e.annual_leave_balance, e.casual_leave_balance, e.sick_leave_balance
        FROM leave_records l
        JOIN employees e ON l.employee_id = e.employee_id
        {where_clause}
        ORDER BY l.rowid DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    bal_idx = {"Annual": 8, "Casual": 9, "Sick": 10}
    return [
        {
            "leave_id": r[0],
            "employee_id": r[1],
            "employee_name": r[2],
            "department": r[3],
            "leave_type": r[4],
            "days": r[5],
            "reason": r[6] or "-",
            "status": r[7],
            "available_balance": r[bal_idx.get(r[4], 8)],
        }
        for r in rows
    ]


def get_all_expense_claims(pending_only: bool = False) -> list[dict]:
    """Fetch expense claims joined with employee details."""
    conn = _get_connection()
    cursor = conn.cursor()
    where_clause = "WHERE c.status LIKE 'Pending%'" if pending_only else ""
    cursor.execute(
        f"""
        SELECT c.claim_id, c.employee_id, e.name, e.department, c.category,
               c.amount_bdt, c.description, c.status
        FROM expense_claims c
        JOIN employees e ON c.employee_id = e.employee_id
        {where_clause}
        ORDER BY c.rowid DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "claim_id": r[0],
            "employee_id": r[1],
            "employee_name": r[2],
            "department": r[3],
            "category": r[4],
            "amount_bdt": float(r[5]),
            "description": r[6] or "-",
            "status": r[7],
        }
        for r in rows
    ]


def review_leave_request(leave_id: str, action: str, note: str = "") -> tuple[bool, str]:
    """Approve or decline a pending leave request. Deducts leave balance on approval."""
    action_clean = action.strip().lower()
    if action_clean not in ("approve", "decline"):
        return False, "Action must be 'approve' or 'decline'."

    valid_types = {
        "Annual": "annual_leave_balance",
        "Casual": "casual_leave_balance",
        "Sick": "sick_leave_balance",
    }

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT employee_id, leave_type, days, status FROM leave_records WHERE leave_id = ?",
        (leave_id.strip().upper(),),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, f"Leave request '{leave_id}' not found."

    emp_id, leave_type, days, current_status = row
    if not current_status.startswith("Pending"):
        conn.close()
        return False, f"Leave request '{leave_id}' is already processed ({current_status})."

    note_suffix = f" — Note: {note.strip()}" if note and note.strip() else ""

    if action_clean == "approve":
        col_name = valid_types.get(leave_type)
        if col_name:
            bal = cursor.execute(
                f"SELECT {col_name} FROM employees WHERE employee_id = ?", (emp_id,)
            ).fetchone()[0]
            if days > bal:
                conn.close()
                return False, f"Insufficient {leave_type} balance ({bal}d left, requested {days}d)."
            cursor.execute(
                f"UPDATE employees SET {col_name} = {col_name} - ? WHERE employee_id = ?",
                (days, emp_id),
            )
        new_status = f"Approved by Manager{note_suffix}"
    else:
        new_status = f"Declined by Manager{note_suffix}"

    cursor.execute(
        "UPDATE leave_records SET status = ? WHERE leave_id = ?",
        (new_status, leave_id.strip().upper()),
    )

    # Send real-time notification to the employee
    notif_id = f"NTF-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    if action_clean == "approve":
        notif_type = "approved"
        notif_title = f"✅ Leave Request Approved ({leave_id.strip().upper()})"
        notif_msg = (
            f"Your {leave_type} Leave request for {days} day(s) has been approved by HR Admin. "
            f"Your leave balance has been updated.{note_suffix}"
        )
    else:
        notif_type = "declined"
        notif_title = f"❌ Leave Request Declined ({leave_id.strip().upper()})"
        notif_msg = (
            f"Your {leave_type} Leave request for {days} day(s) was declined by HR Admin. "
            f"No leave balance was deducted.{note_suffix}"
        )
    cursor.execute(
        "INSERT INTO notifications (notification_id, employee_id, related_id, notif_type, title, message, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
        (notif_id, emp_id, leave_id.strip().upper(), notif_type, notif_title, notif_msg, timestamp),
    )

    conn.commit()
    conn.close()
    return True, f"Leave {leave_id} updated: {new_status}"


def review_expense_claim(claim_id: str, action: str, note: str = "") -> tuple[bool, str]:
    """Approve or decline a pending expense reimbursement claim."""
    action_clean = action.strip().lower()
    if action_clean not in ("approve", "decline"):
        return False, "Action must be 'approve' or 'decline'."

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT employee_id, category, amount_bdt, status FROM expense_claims WHERE claim_id = ?",
        (claim_id.strip().upper(),),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, f"Expense claim '{claim_id}' not found."

    emp_id, category, amount_bdt, current_status = row
    if not current_status.startswith("Pending"):
        conn.close()
        return False, f"Expense claim '{claim_id}' is already processed ({current_status})."

    note_suffix = f" — Note: {note.strip()}" if note and note.strip() else ""
    new_status = (
        f"Approved by Manager{note_suffix}"
        if action_clean == "approve"
        else f"Declined by Manager{note_suffix}"
    )
    cursor.execute(
        "UPDATE expense_claims SET status = ? WHERE claim_id = ?",
        (new_status, claim_id.strip().upper()),
    )

    # Send real-time notification to the employee
    notif_id = f"NTF-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    if action_clean == "approve":
        notif_type = "approved"
        notif_title = f"✅ Expense Claim Approved ({claim_id.strip().upper()})"
        notif_msg = (
            f"Your {category} expense claim of {amount_bdt:,.2f} BDT has been approved by HR Admin "
            f"for reimbursement.{note_suffix}"
        )
    else:
        notif_type = "declined"
        notif_title = f"❌ Expense Claim Declined ({claim_id.strip().upper()})"
        notif_msg = (
            f"Your {category} expense claim of {amount_bdt:,.2f} BDT was declined by HR Admin.{note_suffix}"
        )
    cursor.execute(
        "INSERT INTO notifications (notification_id, employee_id, related_id, notif_type, title, message, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
        (notif_id, emp_id, claim_id.strip().upper(), notif_type, notif_title, notif_msg, timestamp),
    )

    conn.commit()
    conn.close()
    return True, f"Expense {claim_id} updated: {new_status}"


def get_employee_notifications(employee_id: str, unread_only: bool = False) -> list[dict]:
    """Fetch notifications for a specific employee, newest first."""
    conn = _get_connection()
    cursor = conn.cursor()
    where_extra = "AND is_read = 0" if unread_only else ""
    cursor.execute(
        f"""
        SELECT notification_id, employee_id, related_id, notif_type, title, message, is_read, created_at
        FROM notifications
        WHERE employee_id = ? {where_extra}
        ORDER BY rowid DESC
        """,
        (employee_id.strip().upper(),),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "notification_id": r[0],
            "employee_id": r[1],
            "related_id": r[2],
            "notif_type": r[3],
            "title": r[4],
            "message": r[5],
            "is_read": bool(r[6]),
            "created_at": r[7],
        }
        for r in rows
    ]


def get_unread_notification_count(employee_id: str) -> int:
    """Return count of unread notifications for an employee."""
    conn = _get_connection()
    cursor = conn.cursor()
    count = cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE employee_id = ? AND is_read = 0",
        (employee_id.strip().upper(),),
    ).fetchone()[0]
    conn.close()
    return int(count)


def mark_notification_read(notification_id: str) -> None:
    """Mark a single notification as read."""
    conn = _get_connection()
    conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE notification_id = ?",
        (notification_id,),
    )
    conn.commit()
    conn.close()


def mark_all_notifications_read(employee_id: str) -> None:
    """Mark all notifications for an employee as read."""
    conn = _get_connection()
    conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE employee_id = ?",
        (employee_id.strip().upper(),),
    )
    conn.commit()
    conn.close()
