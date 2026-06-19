import sqlite3

def migrate():
    conn = sqlite3.connect("qa_platform_v3.db")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE auth_configs ADD COLUMN landing_url TEXT")
        conn.commit()
        print("Successfully added landing_url column to auth_configs table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column landing_url already exists.")
        else:
            raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
