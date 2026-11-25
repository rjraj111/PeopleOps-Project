import sqlite3
import random
import os

DB_PATH = os.path.join("data", "db", "hr_system.db")

def seed_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS notifications")
    cursor.execute("DROP TABLE IF EXISTS expense_claims")
    cursor.execute("DROP TABLE IF EXISTS leave_records")
    cursor.execute("DROP TABLE IF EXISTS employees")

    # 1. Employees Table (IBM HR Analytics Schema)
    cursor.execute("""
    CREATE TABLE employees (
        employee_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        job_role TEXT NOT NULL,
        job_level INTEGER NOT NULL,
        monthly_income_bdt REAL NOT NULL,
        annual_leave_balance INTEGER NOT NULL,
        casual_leave_balance INTEGER NOT NULL,
        sick_leave_balance INTEGER NOT NULL
    )
    """)

    # 2. Leave Records Table
    cursor.execute("""
    CREATE TABLE leave_records (
        leave_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        leave_type TEXT NOT NULL,
        days INTEGER NOT NULL,
        reason TEXT,
        status TEXT NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    """)

    # 3. Expense Claims Table
    cursor.execute("""
    CREATE TABLE expense_claims (
        claim_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        category TEXT NOT NULL,
        amount_bdt REAL NOT NULL,
        description TEXT,
        status TEXT NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    """)

    # 4. Notifications Table
    cursor.execute("""
    CREATE TABLE notifications (
        notification_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        related_id TEXT,
        notif_type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    """)

    # Seed primary demo users
    demo_users = [
        ("EMP-101", "Jahedul Islam", "Engineering", "Software Engineer", 2, 85000.0, 12, 8, 14),
        ("EMP-102", "Rahim Uddin", "Product", "Product Manager", 3, 125000.0, 10, 5, 11),
    ]
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", demo_users)

    # Seed remaining 1,468 IBM HR synthetic records (Total = 1,470)
    departments = ["Engineering", "Sales", "Research & Development", "Human Resources", "Finance"]
    roles = ["Software Engineer", "Sales Executive", "Research Scientist", "HR Specialist", "Analyst"]
    
    bulk_employees = []
    for i in range(103, 1571):
        emp_id = f"EMP-{i}"
        dept = random.choice(departments)
        role = random.choice(roles)
        lvl = random.randint(1, 5)
        income = round(random.uniform(45000, 180000), 2)
        bulk_employees.append((emp_id, f"Employee {i}", dept, role, lvl, income, 15, 10, 14))

    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", bulk_employees)

    # Seed initial sample records (including pending High-Risk cases for Admin Panel demo)
    cursor.execute("INSERT INTO expense_claims VALUES ('CLM-1001', 'EMP-101', 'Internet', 1200.0, 'Monthly broadband bill', 'Approved')")
    cursor.execute("INSERT INTO expense_claims VALUES ('CLM-1002', 'EMP-102', 'Client Meals', 7500.0, 'Enterprise client dinner with 6 stakeholders', 'Pending Manager Approval (High-Risk Escalation: >5,000 BDT)')")
    cursor.execute("INSERT INTO leave_records VALUES ('LV-1001', 'EMP-101', 'Annual', 3, 'Family trip', 'Approved')")
    cursor.execute("INSERT INTO leave_records VALUES ('LV-1002', 'EMP-102', 'Annual', 5, 'International family vacation', 'Pending Manager Approval (High-Risk Escalation: >3 days)')")
    cursor.execute("INSERT INTO notifications VALUES ('NTF-1001', 'EMP-101', 'LV-1001', 'approved', '✅ Leave Request Approved (LV-1001)', 'Your Annual Leave request for 3 day(s) was auto-approved under standard HR policy.', 0, '2026-11-24 10:30')")
    cursor.execute("INSERT INTO notifications VALUES ('NTF-1002', 'EMP-102', 'LV-1002', 'info', '⏳ Escalated to HR Admin (LV-1002)', 'Your 5-day Annual Leave request exceeds 3 consecutive days and has been routed to the Admin Panel for manager review.', 0, '2026-11-24 14:15')")

    conn.commit()
    conn.close()
    print(f"Database seeded successfully at {DB_PATH} with 1,470 employee records!")

if __name__ == "__main__":
    seed_database()