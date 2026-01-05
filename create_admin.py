import sqlite3
import os
from werkzeug.security import generate_password_hash

# Path to your database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'portfolio.db')

def create_admin():
    # 1. Configuration
    admin_email = "admin@tukakombe.com"
    admin_password = "Tukakombe!"
    
    # Use the same hashing method your auth system uses
    # If you are using plain werkzeug, this is the standard:
    hashed_password = generate_password_hash(admin_password)

    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run initialize_db first!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 2. Check if admin already exists
        c.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
        existing_user = c.fetchone()

        if existing_user:
            print(f"User {admin_email} already exists. Updating password and role...")
            c.execute("""
                UPDATE users 
                SET password = ?, role = 'super_admin' 
                WHERE email = ?
            """, (hashed_password, admin_email))
        else:
            print(f"Creating new admin user: {admin_email}...")
            c.execute("""
                INSERT INTO users (email, password, role) 
                VALUES (?, ?, ?)
            """, (admin_email, hashed_password, 'super_admin'))

        conn.commit()
        print("Success! You can now log in at /admin/login")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_admin()