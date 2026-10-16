def validate_question(question):
    errors = []

    if not question.get("id"):
        errors.append("Question ID is missing.")

    if not question.get("question_text"):
        errors.append("Question text is missing.")

    q_type = question.get("question_type")
    options = question.get("options")
    
    if q_type == "mcq_single":
        if not options:
            errors.append("Options are missing for MCQ.")
        elif len(options) != 4:
            errors.append("Question must have exactly 4 options.")
            
    correct_answer = question.get("correct_answer")
    if not correct_answer:
        errors.append("Correct answer is missing.")
    elif q_type == "mcq_single" and options and correct_answer not in options:
        errors.append("Correct answer is not present in the options.")

    required_fields = ["subject", "chapter"]
    for field in required_fields:
        if not question.get(field):
            errors.append(f"{field} is missing.")

    if errors:
        return False, errors

    return True, []


def check_duplicates(questions):

    seen = set()
    duplicates = []

    for question in questions:

        text = question.get("question", "").strip().lower()

        if text in seen:
            duplicates.append(question.get("id"))
        else:
            seen.add(text)

    return duplicates