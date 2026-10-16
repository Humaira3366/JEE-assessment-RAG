import json
import random
import os
from retrieval import retrieve_questions
from validation import validate_question

def load_weightage():
    weightage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'jee_chapter_weightage.json')
    try:
        with open(weightage_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def generate_jee_paper(questions):
    weightage_data = load_weightage()
    topic_weightage = {}
    for subject, classes in weightage_data.items():
        topic_weightage[subject] = {}
        for cls, topics in classes.items():
            for topic, weight_str in topics.items():
                try:
                    weight = float(weight_str.replace('%', '')) / 100.0
                except ValueError:
                    weight = 0.01
                topic_weightage[subject][topic] = weight

    available = {'Mathematics': {'mcq_single': [], 'numerical': []},
                 'Physics': {'mcq_single': [], 'numerical': []},
                 'Chemistry': {'mcq_single': [], 'numerical': []}}
                 
    for q in questions:
        sub = q.get('subject')
        qtype = q.get('question_type')
        if sub in available and qtype in available[sub]:
            available[sub][qtype].append(q)

    paper = []
    
    for subject in ['Physics', 'Chemistry', 'Mathematics']:
        req_mcq = 20
        req_num = 10
        
        sub_mcqs = available[subject]['mcq_single']
        sub_nums = available[subject]['numerical']
        
        def pick_questions(pool, req_count):
            if not pool: return []
            pick_count = min(req_count, len(pool))
            weighted_pool = []
            for q in pool:
                topic = q.get('chapter', '')
                w = topic_weightage.get(subject, {}).get(topic, 0.01)
                weighted_pool.append((q, w))
            
            # Sort by weight * random factor to probabilistically favor high weight topics
            weighted_pool.sort(key=lambda x: x[1] * random.random(), reverse=True)
            return [x[0] for x in weighted_pool[:pick_count]]
            
        selected_mcqs = pick_questions(sub_mcqs, req_mcq)
        selected_nums = pick_questions(sub_nums, req_num)
        
        paper.extend(selected_mcqs)
        paper.extend(selected_nums)
        
    return paper

def generate_assessment(
    questions,
    subject=None,
    chapter=None,
    difficulty=None,
    number=5,
    is_jee_paper=False
):
    if is_jee_paper:
        retrieved_questions = generate_jee_paper(questions)
    else:
        # Retrieve all matching questions first, without limiting to number
        # We will limit AFTER validation.
        retrieved_questions = retrieve_questions(
            questions,
            subject=subject,
            chapter=chapter,
            difficulty=difficulty,
            number=1000  # get all matching
        )

    valid_questions = []
    for question in retrieved_questions:
        valid, errors = validate_question(question)
        if valid:
            valid_questions.append(question)
            
    # Now limit to the requested number (only for generic test)
    if not is_jee_paper:
        valid_questions = valid_questions[:number]

    questions_for_user = []
    for question in valid_questions:
        question_copy = question.copy()
        question_copy.pop("correct_answer", None)
        questions_for_user.append(question_copy)

    return {
        "subject": subject if not is_jee_paper else "JEE Mock Paper",
        "chapter": chapter if not is_jee_paper else "All",
        "difficulty": difficulty,
        "is_jee_paper": is_jee_paper,
        "number_of_questions": len(questions_for_user),
        "questions": questions_for_user
    }