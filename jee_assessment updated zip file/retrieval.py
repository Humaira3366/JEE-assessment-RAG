import json


def get_db_connection():
    import psycopg2
    import os
    from dotenv import load_dotenv
    # Ensure environment variables are loaded
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    
    return psycopg2.connect(
        host="aws-0-ap-northeast-1.pooler.supabase.com",
        port=5432,
        database="postgres",
        user="postgres.knbiciilhfomwfzxqthl",
        password="6jkrc39v@Hum",
        sslmode="require"
    )

def load_questions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, question_number, question_type, question_text, options, answer, solution, chapter_topic FROM questions")
    rows = cursor.fetchall()
    
    questions = []
    for row in rows:
        options = row[5]
        if isinstance(options, str):
            import json
            try:
                options = json.loads(options)
            except Exception:
                options = {}
                
        questions.append({
            "id": row[0],
            "subject": row[1],
            "question_number": row[2],
            "question_type": row[3],
            "question_text": row[4],
            "options": options,
            "correct_answer": row[6],
            "solution": row[7],
            "chapter": row[8]
        })
        
    cursor.close()
    conn.close()
    return questions


def retrieve_questions(
    questions,
    subject=None,
    chapter=None,
    difficulty=None,
    number=5
):
    results = []

    for question in questions:

        if subject and question.get("subject", "").lower() != subject.lower():
            continue

        if chapter and question.get("chapter", "").lower() != chapter.lower():
            continue

        if difficulty and question.get("difficulty", "").lower() != difficulty.lower():
            continue

        results.append(question)

    if len(results) < number:
        print(
            f"Warning: Only {len(results)} questions found, "
            f"but {number} were requested."
        )

    return results[:number]