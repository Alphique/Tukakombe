# utils/database.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'portfolio.db')

def get_db_connection():
    """Return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    """Create tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # ------------------------------
    # USERS TABLE
    # ------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'client',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ------------------------------
    # FINANCE LOANS TABLE
    # ------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            business_name TEXT NOT NULL,
            loan_amount REAL NOT NULL,
            loan_purpose TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # ------------------------------
    # BLOGS TABLE
    # ------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # ------------------------------
    # COMMENTS TABLE
    # ------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blog_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (blog_id) REFERENCES blogs(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # ==================================================
    # 🔥 MARKETPLACE TABLES (NEW)
    # ==================================================

    # ------------------------------
    # PRODUCTS TABLE
    # ------------------------------
    cursor.execute('''
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
    ''')

    # ------------------------------
    # PRODUCT INQUIRIES (optional but powerful)
    # ------------------------------
    cursor.execute('''
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
    ''')

    conn.commit()
    conn.close()
