from retrieval import load_questions, retrieve_questions
from validation import validate_question
from evaluation import evaluate_test

from performance_history import (
    create_performance_record,
    save_performance_record,
    get_performance_history
)


# Load questions
questions = load_questions()


# Retrieve Physics questions
retrieved = retrieve_questions(
    questions,
    subject="Physics",
    number=5
)

print("Retrieved questions:", len(retrieved))


# Validate retrieved questions
valid_questions = []

for question in retrieved:

    valid, errors = validate_question(question)

    if valid:
        valid_questions.append(question)

    else:
        print("Invalid question:", question["id"])
        print("Errors:", errors)


print("Valid questions:", len(valid_questions))


# Make sure enough questions are available for the test
if len(valid_questions) >= 3:

    student_answers = {
        valid_questions[0]["id"]: valid_questions[0]["correct_answer"],
        valid_questions[1]["id"]: "Wrong Answer",
        valid_questions[2]["id"]: valid_questions[2]["correct_answer"]
    }

    # Evaluate the answers
    result = evaluate_test(
        valid_questions[:3],
        student_answers
    )

    print("\n--- Final Evaluation ---")
    print("Correct:", result["correct"])
    print("Wrong:", result["wrong"])
    print("Unattempted:", result["unattempted"])
    print("Final Score:", result["marks"])

else:

    print("Not enough valid questions for integration test.")

    from performance_history import (
    create_performance_record,
    save_performance_record,
    get_performance_history
)


history_record = create_performance_record(
    result,
    time_taken_minutes=40
)

save_performance_record(history_record)

print("\n--- Performance History ---")
print(get_performance_history())