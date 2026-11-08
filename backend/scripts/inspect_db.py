import sqlite3

conn = sqlite3.connect("travelsenseai.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in SQLite database:", tables)

for table in tables:
    cursor.execute(f"PRAGMA table_info({table});")
    columns = [f"{col[1]} ({col[2]})" for col in cursor.fetchall()]
    print(f"\nTable: {table}")
    print("  Columns:", ", ".join(columns))

