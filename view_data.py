import os
import psycopg2
import json

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

    print("============================================================")
    print("TABLE 1: QUESTIONS")
    print("============================================================")
    
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'questions';")
    q_columns = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM questions LIMIT 1;")
    q_row = cursor.fetchone()
    
    if q_row:
        q_dict = dict(zip(q_columns, q_row))
        for key, value in q_dict.items():
            print(f"--- {key.upper()} ---")
            print(f"{value}")
            print("-" * 50)
    else:
        print("No questions found.")


    print("\n============================================================")
    print("TABLE 2: QUESTION_EMBEDDINGS (Vector AI Data)")
    print("============================================================")
    
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'question_embeddings';")
    e_columns = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM question_embeddings LIMIT 1;")
    e_row = cursor.fetchone()
    
    if e_row:
        e_dict = dict(zip(e_columns, e_row))
        for key, value in e_dict.items():
            print(f"--- {key.upper()} ---")
            
            # Embeddings are huge arrays (384 numbers), so we will just show the length and first 3 numbers
            if key == 'embedding':
                # Parse string representation of array if needed
                if isinstance(value, str):
                    vec = json.loads(value)
                else:
                    vec = value
                print(f"   [Vector Array of {len(vec)} numbers]: {vec[:3]} ...")
            else:
                print(f"   {value}")
            print("-" * 50)
    else:
        print("No embeddings found.")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
