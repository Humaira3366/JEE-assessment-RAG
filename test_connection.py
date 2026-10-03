import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("SUPABASE_DB_PASSWORD")

if not password:
    raise ValueError("SUPABASE_DB_PASSWORD is not set")

conn = psycopg2.connect(
    host="aws-0-ap-northeast-1.pooler.supabase.com",
    port=5432,
    database="postgres",
    user="postgres.knbiciilhfomwfzxqthl",
    password=password,
    sslmode="require",
    connect_timeout=10
)

print("✅ Connected to Supabase!")

cursor = conn.cursor()
cursor.execute("SELECT current_database(), current_user;")

print(cursor.fetchone())

cursor.close()
conn.close()