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
    
    print("Adding 'chapter_topic' column to questions table...")
    cursor.execute("ALTER TABLE questions ADD COLUMN IF NOT EXISTS chapter_topic TEXT;")
    conn.commit()
    
    print("✅ Column added successfully!")
    
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
