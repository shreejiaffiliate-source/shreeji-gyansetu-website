# Save as find_data.py
import sqlite3

def find_my_lessons():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    
    print("--- Database Table Scan ---")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Table: {table} | Rows: {count}")
    
    conn.close()

if __name__ == '__main__':
    find_my_lessons()