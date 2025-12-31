import os
import sqlite3
from auth.utils import hash_password

# Path to your SQLite database
DB_PATH = os.path.join(os.path.dirname(__file__), 'portfolio.db')

# Admin credentials
ADMIN_EMAIL = "admin@tukakombe.com"
ADMIN_PASSWORD = "Tukakombe!"
ADMIN_ROLE = "super_admin"  # or "admin" if you prefer

def create_admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Hash the password
    hashed_password = hash_password(ADMIN_PASSWORD)

    try:
        cursor.execute("""
            INSERT INTO users (email, password, role, is_active)
            VALUES (?, ?, ?, 1)
        """, (ADMIN_EMAIL, hashed_password, ADMIN_ROLE))
        conn.commit()
        print(f"Admin user {ADMIN_EMAIL} created successfully!")
    except sqlite3.IntegrityError:
        print(f"User {ADMIN_EMAIL} already exists.")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()
