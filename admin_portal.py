import streamlit as st
import fitz  # PyMuPDF
import base64
import json
import psycopg2
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import os

# Set up page config
st.set_page_config(page_title="Admin Ingestion Portal", layout="wide")

st.title("🚀 Admin Ingestion Portal")
st.write("Upload a JEE PDF paper. The AI will read the images, extract questions and solutions, generate AI embeddings, and save everything (including topics!) to the database.")

from dotenv import load_dotenv
load_dotenv()

# 1. Initialize API Clients
client_gemini = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
)

client_groq = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
)

# 2. Load Embedding Model (Cached so it only loads once)
@st.cache_resource
def load_embedding_model():
    # Using a fast, standard embedding model that runs locally
    return SentenceTransformer("all-MiniLM-L6-v2")

embedding_model = load_embedding_model()

def get_db_connection():
    return psycopg2.connect(
        host="aws-0-ap-northeast-1.pooler.supabase.com",
        port=5432,
        database="postgres",
        user="postgres.knbiciilhfomwfzxqthl",
        password="6jkrc39v@Hum",
        sslmode="require"
    )

uploaded_file = st.file_uploader("Upload JEE Paper (PDF)", type=["pdf"])

if uploaded_file is not None:
    if st.button("Start AI Ingestion"):
        
        # Load the chapters from the JSON we just created to constrain the LLM
        with open("jee_chapter_weightage.json", "r") as f:
            chapters_data = json.load(f)
            
        # We pass the full nested structure (Subject -> Class -> Chapters) to the LLM 
        # so it only picks a Mathematics chapter if the subject is Mathematics.
        chapters_str = json.dumps(chapters_data, indent=2)
        
        # Read the PDF using PyMuPDF
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        progress_bar = st.progress(0)
        
        for page_num in range(len(doc)):
            with st.spinner(f"Extracting questions from Page {page_num + 1}..."):
                # Phase 1: PDF to Image conversion
                page = doc[page_num]
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("jpeg")
                base64_image = base64.b64encode(img_bytes).decode("utf-8")
                
                # Phase 1: Gemini Multimodal Extraction
                prompt = f"""
                You are an expert JEE Physics, Chemistry, and Mathematics professor. Look at this image of a JEE paper.
                Extract ALL the questions from it. Ignore headers and footers.
                CRITICAL INSTRUCTION: For each question you extract, you MUST also SOLVE it yourself to figure out the correct answer.
                Return a JSON array of objects. 
                Each object MUST exactly match this format:
                {{
                  "question_number": (integer),
                  "subject": (string: "Physics", "Chemistry", or "Mathematics"),
                  "question_type": (string: "mcq_single" or "numerical"),
                  "question_text": (string: the full text of the question, including equations),
                  "options": (JSON object mapping A, B, C, D to their text. Leave empty if numerical),
                  "answer": (string: SOLVE the question and provide ONLY the correct option letter A/B/C/D, or the final numerical value),
                  "solution": (string: leave this as an empty string ""),
                  "chapter_topic": (string: First, look at the "subject" you determined. Then, choose EXACTLY ONE chapter name from the provided hierarchy below for that specific subject. DO NOT pick a Physics chapter for a Math question.\nHierarchy: {chapters_str})
                }}
                Ensure the output is ONLY a valid JSON array, without any markdown formatting like ```json.
                """
                
                try:
                    if page_num % 2 == 0:
                        active_client = client_gemini
                        active_model = os.environ.get("OPENAI_MODEL", "gemini-2.5-flash")
                    else:
                        active_client = client_groq
                        active_model = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")

                    response = active_client.chat.completions.create(
                        model=active_model,
                        max_tokens=8192,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]
                            }
                        ]
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    # Clean up markdown if Gemini decides to include it
                    if result_text.startswith("```json"):
                        result_text = result_text[7:-3]
                    elif result_text.startswith("```"):
                        result_text = result_text[3:-3]
                        
                    questions = json.loads(result_text)
                    
                    # Fallback if Gemini wraps it in an object instead of array
                    if isinstance(questions, dict) and "questions" in questions:
                        questions = questions["questions"]
                        
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    st.write(f"✅ Page {page_num + 1}: Found {len(questions)} questions.")
                    
                    for q in questions:
                        # Phase 3: Insert the Human-Readable Text into Database
                        cursor.execute(
                            '''
                            INSERT INTO questions (subject, question_number, question_type, question_text, options, answer, solution, chapter_topic, page_number)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id;
                            ''',
                            (q.get("subject"), q.get("question_number"), q.get("question_type"), 
                             q.get("question_text"), json.dumps(q.get("options", {})), 
                             str(q.get("answer")), q.get("solution"), q.get("chapter_topic"), page_num+1)
                        )
                        question_id = cursor.fetchone()[0]
                        
                        # Phase 2: Generate Vectors (Embeddings)
                        # Only embedding the question text (and options), excluding the answer as requested
                        embed_text = f"Question: {q.get('question_text')} Options: {json.dumps(q.get('options', {}))}"
                        # This turns the text into a 384-dimensional mathematical array
                        embedding = embedding_model.encode(embed_text).tolist()
                        
                        # Phase 3: Insert the Vectors into Database
                        cursor.execute(
                            '''
                            INSERT INTO question_embeddings (question_id, chunk_type, content, embedding)
                            VALUES (%s, %s, %s, %s);
                            ''',
                            (question_id, 'full_question', embed_text, embedding)
                        )
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                except Exception as e:
                    st.error(f"Error processing page {page_num + 1}: {str(e)}")
                
                # IMPORTANT: Wait 4 seconds before sending the next page to avoid 503 errors on the free API tier
                import time
                time.sleep(4)
                    
            progress_bar.progress((page_num + 1) / len(doc))
            
        st.balloons()
        st.success("🎉 Completely finished Phase 1, Phase 2, and Phase 3! Data is live in Supabase!")
