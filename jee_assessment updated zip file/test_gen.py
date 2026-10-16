import os
import django
import sys

sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from retrieval import load_questions
from assessment_generator import generate_assessment

q = load_questions()
print(f"Loaded {len(q)} questions from DB.")

test = generate_assessment(q, number=2)
print("Generic Test generated with", test["number_of_questions"], "questions.")

jee = generate_assessment(q, is_jee_paper=True)
print("JEE Test generated with", jee["number_of_questions"], "questions.")
