import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("SUPABASE_DB_PASSWORD")

conn = psycopg2.connect(
    host="aws-0-ap-northeast-1.pooler.supabase.com",
    port=5432,
    database="postgres",
    user="postgres.knbiciilhfomwfzxqthl",
    password=password,
    sslmode="require"
)

cursor = conn.cursor()

cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('questions', 'question_embeddings')
    ORDER BY table_name;
""")

tables = cursor.fetchall()

print("Tables found:")
for table in tables:
    print("✅", table[0])

cursor.close()
conn.close()