import os
import psycopg2

try:
    conn = psycopg2.connect(
        host="aws-0-ap-northeast-1.pooler.supabase.com",
        port=5432,
        database="postgres",
        user="postgres.knbiciilhfomwfzxqthl",
        password="6jkrc39v@Hum",
        sslmode="require"
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    print("Tables in database:", tables)
    
    # Check what's in chapter_weightage or similar table
    weightage_tables = [t[0] for t in tables if 'weightage' in t[0].lower()]
    for wt in weightage_tables:
        cursor.execute(f"SELECT * FROM {wt} LIMIT 5")
        rows = cursor.fetchall()
        
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{wt}'")
        cols = [c[0] for c in cursor.fetchall()]
        print(f"\nTable {wt} columns:", cols)
        print(f"Table {wt} sample rows:", rows)

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
