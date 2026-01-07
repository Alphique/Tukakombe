import sqlite3
import os

# 1. Try local directory first, then the parent directory
possible_paths = [
    os.path.join(os.getcwd(), 'portfolio.db'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portfolio.db'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'portfolio.db')
]

DB_PATH = None
for path in possible_paths:
    if os.path.exists(path):
        DB_PATH = path
        break

def migrate_database():
    if not DB_PATH:
        print("❌ Database not found!")
        print("I checked these locations:")
        for p in possible_paths: print(f"  - {p}")
        return

    print(f"✅ Found database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Columns we need to ensure exist
    new_columns = [
        ("contact_person_position", "TEXT"),
        ("business_years", "INTEGER"),
        ("monthly_revenue", "REAL DEFAULT 0.0")
    ]

    print(f"--- Starting Migration ---")

    for col_name, col_type in new_columns:
        try:
            # Check existing columns
            cursor.execute("PRAGMA table_info(business_loan_details)")
            columns = [info[1] for info in cursor.fetchall()]

            if col_name not in columns:
                print(f"Adding column '{col_name}'...")
                cursor.execute(f"ALTER TABLE business_loan_details ADD COLUMN {col_name} {col_type}")
                print(f"✅ Column '{col_name}' added.")
            else:
                print(f"ℹ️ Column '{col_name}' already exists.")

        except sqlite3.Error as e:
            print(f"❌ Error: {e}")

    conn.commit()
    conn.close()
    print("--- Migration Complete ---")

if __name__ == "__main__":
    migrate_database()