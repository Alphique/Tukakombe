# utils/database.py

import sqlite3
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ==================================================
# PATHS & UPLOAD FOLDERS
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'portfolio.db')

UPLOAD_BASE = os.path.join(BASE_DIR, '..', 'static', 'uploads')
UPLOAD_FOLDERS = [
    UPLOAD_BASE,
    f"{UPLOAD_BASE}/blogs",
    f"{UPLOAD_BASE}/products",
    f"{UPLOAD_BASE}/loans",
    f"{UPLOAD_BASE}/collateral",
    f"{UPLOAD_BASE}/signatures"
]

for folder in UPLOAD_FOLDERS:
    os.makedirs(folder, exist_ok=True)

# ==================================================
# DATABASE CONNECTION
# ==================================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ==================================================
# DATABASE INITIALIZATION
# ==================================================
def initialize_db():
    conn = get_db_connection()
    c = conn.cursor()

    # ---------------- USERS ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- BLOGS ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            status TEXT DEFAULT 'published',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # ---------------- COMMENTS ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blog_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (blog_id) REFERENCES blogs(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ---------------- PRODUCTS ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS product_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ---------------- LOAN APPLICATIONS ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS loan_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_number TEXT UNIQUE NOT NULL,
            loan_type TEXT CHECK(loan_type IN ('personal','business')) NOT NULL,
            status TEXT DEFAULT 'pending',
            user_id INTEGER,
            interest_rate REAL DEFAULT 0.30,
            total_repayment REAL,
            admin_notes TEXT,
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP,
            decision_date TIMESTAMP,
            decision_by INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ---------------- PERSONAL LOANS ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS personal_loan_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER UNIQUE NOT NULL,
            loan_amount REAL NOT NULL,
            purpose TEXT NOT NULL,
            repayment_period_days INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            date_of_birth DATE,
            nrc_number TEXT,
            email TEXT,
            phone_number TEXT,
            residential_address TEXT,
            terms_accepted INTEGER DEFAULT 0,
            agreement_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES loan_applications(id) ON DELETE CASCADE
        )
    """)

    # ---------------- BUSINESS LOANS ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS business_loan_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER UNIQUE NOT NULL,
            business_name TEXT NOT NULL,
            business_registration_number TEXT NOT NULL,
            loan_amount REAL NOT NULL,
            purpose TEXT NOT NULL,
            repayment_period_days INTEGER NOT NULL,
            contact_person_name TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            business_address TEXT,
            terms_accepted INTEGER DEFAULT 0,
            agreement_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES loan_applications(id) ON DELETE CASCADE
        )
    """)

    # ---------------- COLLATERAL ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS collateral_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            loan_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            item_type TEXT,
            estimated_value REAL,
            condition_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES loan_applications(id) ON DELETE CASCADE
        )
    """)

    # ---------------- ATTACHMENTS ----------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS application_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            document_category TEXT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES loan_applications(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")


# ==================================================
# USER AUTH HELPERS
# ==================================================
def create_user(email, password, role='user'):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        hashed = generate_password_hash(password)
        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (email, hashed, role))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        print(f"[DB ERROR] create_user: {e}")
        return None
    finally:
        conn.close()

def verify_user(email, password):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        if user and check_password_hash(user['password'], password):
            return dict(user)
        return None
    finally:
        conn.close()


# ==================================================
# LOAN HELPERS
# ==================================================
def generate_application_number(loan_type):
    prefix = "PERS" if loan_type == "personal" else "BUS"
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

def create_loan_application(user_id, loan_type):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        app_number = generate_application_number(loan_type)
        c.execute("""
            INSERT INTO loan_applications (application_number, loan_type, user_id)
            VALUES (?, ?, ?)
        """, (app_number, loan_type, user_id))
        conn.commit()
        return c.lastrowid, app_number
    except sqlite3.Error as e:
        print(f"[DB ERROR] create_loan_application: {e}")
        return None, None
    finally:
        conn.close()

def save_personal_loan_details(application_id, data):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO personal_loan_details (
                application_id, loan_amount, purpose, repayment_period_days,
                full_name, date_of_birth, nrc_number, email, phone_number,
                residential_address, terms_accepted, agreement_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            application_id, data.get('loan_amount'), data.get('purpose'),
            data.get('repayment_period', 30), data.get('full_name'),
            data.get('dob'), data.get('nrc'), data.get('email'),
            data.get('phone'), data.get('address'), 1, datetime.now()
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB ERROR] save_personal_loan_details: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ==================================================
# BUSINESS LOAN HELPERS
def save_business_loan_details(application_id, data):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO business_loan_details (
                application_id, business_name, business_registration_number,
                loan_amount, purpose, repayment_period_days, contact_person_name,
                contact_email, contact_phone, business_address, terms_accepted, agreement_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            application_id, data.get('business_name'), data.get('reg_number'),
            data.get('loan_amount'), data.get('purpose'), data.get('repayment_period', 30),
            data.get('contact_name'), data.get('email'), data.get('phone'),
            data.get('address'), 1, datetime.now()
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB ERROR] save_business_loan_details: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ==================================================
# COLLATERAL HELPERS
def save_collateral_items(application_id, loan_type, items_list):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        for item in items_list:
            c.execute("""
                INSERT INTO collateral_items (
                    application_id, loan_type, item_name, item_type, 
                    estimated_value, condition_description
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (application_id, loan_type, item.get('name'), 
                  item.get('type'), item.get('value'), item.get('condition')))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB ERROR] save_collateral_items: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ==================================================
# ATTACHMENT HELPERS
def save_application_attachments(application_id, category, filename, filepath):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO application_attachments (application_id, document_category, file_name, file_path)
            VALUES (?, ?, ?, ?)
        """, (application_id, category, filename, filepath))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB ERROR] save_application_attachments: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ==================================================
# ADMIN LOAN DECISION HELPERS
def update_loan_status(loan_id, status, admin_notes, admin_id):
    """
    Updates the loan application with the admin's decision.
    Links the action to the admin's user ID and sets the timestamp.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("""
            UPDATE loan_applications 
            SET status = ?, 
                admin_notes = ?, 
                decision_by = ?, 
                decision_date = CURRENT_TIMESTAMP,
                updated_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, admin_notes, admin_id, loan_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB ERROR] update_loan_status: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ==================================================
# CALCULATION HELPERS
def calculate_total_repayment(loan_amount, rate=0.30):
    try:
        principal = float(loan_amount)
        total = principal + (principal * float(rate))
        return round(total, 2)
    except (ValueError, TypeError):
        return 0.0
