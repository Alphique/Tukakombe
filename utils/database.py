# utils/database.py
import sqlite3
import os

# ==================================================
# DATABASE PATH
# ==================================================
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'portfolio.db')

# ==================================================
# UPLOAD FOLDERS
# ==================================================
BLOG_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'blogs')
PRODUCT_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'products')
os.makedirs(BLOG_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PRODUCT_UPLOAD_FOLDER, exist_ok=True)

# ==================================================
# DATABASE CONNECTION
# ==================================================
def get_db_connection():
    """
    Returns a SQLite connection with Row factory enabled
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================================================
# DATABASE INITIALIZATION
# ==================================================
def initialize_db():
    """
    Create all database tables.
    MUST be called once on app startup.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------
    # USERS
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'client',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------
    # LOAN APPLICATIONS
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            business_name TEXT NOT NULL,
            loan_amount REAL NOT NULL,
            loan_purpose TEXT,
            status TEXT DEFAULT 'pending',
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # -----------------------------
    # LOAN ATTACHMENTS
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loan_id) REFERENCES loan_applications(id)
        )
    """)

    # -----------------------------
    # BLOGS
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            status TEXT DEFAULT 'draft',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # -----------------------------
    # COMMENTS
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blog_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (blog_id) REFERENCES blogs(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # -----------------------------
    # PRODUCTS
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image TEXT,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # -----------------------------
    # PRODUCT INQUIRIES
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER,
            name TEXT,
            email TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # -----------------------------
    # FINALIZE
    # -----------------------------
    conn.commit()
    conn.close()

def initialize_db():
    """
    Create all database tables and handle migrations.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. RUN YOUR EXISTING CREATE STATEMENTS
    # (Users, Loans, etc. - keep them as they are)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            status TEXT DEFAULT 'draft',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # 2. THE FIX: CHECK IF 'STATUS' COLUMN ACTUALLY EXISTS
    # This handles cases where the table was created yesterday without the column.
    cursor.execute("PRAGMA table_info(blogs)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'status' not in columns:
        print("Migrating database: Adding 'status' column to blogs table...")
        cursor.execute("ALTER TABLE blogs ADD COLUMN status TEXT DEFAULT 'draft'")

    # 3. FINALIZE
    conn.commit()
    conn.close()
    print("Database initialized and verified.")