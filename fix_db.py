from utils.database import get_db_connection

def add_column():
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
        conn.commit()
        print("Column 'is_active' added successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_column()