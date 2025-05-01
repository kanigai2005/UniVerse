import os
import sqlite3

def apply_schema(db_path, schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        print(f"Schema applied successfully to {db_path}")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "explore.db")
    schema_path = os.path.join(base_dir, "schema.sql")
    print(schema_path)
    print(db_path)
    apply_schema(db_path, schema_path)
