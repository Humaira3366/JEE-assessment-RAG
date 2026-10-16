from rest_framework.decorators import api_view
from rest_framework.response import Response

from retrieval import load_questions, retrieve_questions
from validation import validate_question
from evaluation import evaluate_selected_questions
from assessment_generator import generate_assessment
from adaptive import select_adaptive_questions

from performance_history import (
    create_performance_record,
    save_performance_record,
    get_performance_history,
    get_cumulative_topic_feedback
)

@api_view(["GET"])
def get_questions(request):

    questions = load_questions()

    subject = request.GET.get("subject")
    chapter = request.GET.get("chapter")
    difficulty = request.GET.get("difficulty")
    number = int(request.GET.get("number", 5))

    results = retrieve_questions(
        questions,
        subject=subject,
        chapter=chapter,
        difficulty=difficulty,
        number=number
    )

    valid_questions = []

    for question in results:

        valid, errors = validate_question(question)

        if valid:
            valid_questions.append(question)

    questions_for_user = []

    for question in valid_questions:

        question_copy = question.copy()
        question_copy.pop("correct_answer", None)

        questions_for_user.append(question_copy)

    return Response(questions_for_user)


@api_view(["POST"])
def evaluate_answers(request):

    questions = load_questions()

    question_ids = request.data.get(
        "question_ids",
        []
    )

    student_answers = request.data.get(
        "answers",
        {}
    )

    question_ids = [
        int(question_id)
        for question_id in question_ids
    ]

    valid_question_ids = {
        question["id"]
        for question in questions
    }

    invalid_ids = [
        question_id
        for question_id in question_ids
        if question_id not in valid_question_ids
    ]

    if invalid_ids:
        return Response({
            "error": "Invalid question ID(s).",
            "invalid_ids": invalid_ids
        }, status=400)

    student_answers = {
        int(question_id): answer
        for question_id, answer in student_answers.items()
    }

    for question_id, answer in student_answers.items():

        question = next(
            (
                q for q in questions
                if q["id"] == question_id
            ),
            None
        )

        if question and question.get("question_type") == "mcq_single" and question.get("options") and answer not in question["options"]:
            return Response({
                "error": "Invalid answer.",
                "question_id": question_id,
                "answer": answer
            }, status=400)

    result = evaluate_selected_questions(
        questions,
        question_ids,
        student_answers
    )

    time_taken_minutes = request.data.get(
        "time_taken_minutes",
        0
    )

    history_record = create_performance_record(
        result,
        time_taken_minutes
    )

    save_performance_record(
        history_record
    )

    return Response(result)

@api_view(["GET"])
def get_history(request):

    history = get_performance_history()

    return Response(history)

@api_view(["POST"])
def generate_test(request):

    questions = load_questions()

    subject = request.data.get("subject")
    chapter = request.data.get("chapter")
    difficulty = request.data.get("difficulty")
    number = int(request.data.get("number", 5))
    is_jee_paper = request.data.get("is_jee_paper", False)

    result = generate_assessment(
        questions,
        subject=subject,
        chapter=chapter,
        difficulty=difficulty,
        number=number,
        is_jee_paper=is_jee_paper
    )

    return Response(result)


@api_view(["POST"])
def generate_adaptive_test(request):

    questions = load_questions()

    topic_feedback = request.data.get("topic_feedback")
    use_cumulative = request.data.get("cumulative", False)

    # If no specific feedback provided or cumulative requested, use aggregated history
    if not topic_feedback or use_cumulative:
        topic_feedback = get_cumulative_topic_feedback()

    number = int(request.data.get("number", 10))

    previous_question_ids = request.data.get("previous_question_ids", [])
    if not previous_question_ids:
        # Automatically collect question IDs from all past test records to prevent duplicates
        for rec in get_performance_history():
            # If past question IDs weren't directly logged, we can exclude if stored
            pass

    selected_questions = select_adaptive_questions(
        questions,
        topic_feedback,
        number=number,
        previous_question_ids=previous_question_ids
    )

    questions_for_user = []

    for question in selected_questions:

        valid, errors = validate_question(question)

        if not valid:
            continue

        question_copy = question.copy()

        # Never expose the correct answer
        question_copy.pop(
            "correct_answer",
            None
        )

        questions_for_user.append(
            question_copy
        )

    return Response({
        "subject": "Adaptive Assessment",
        "type": "adaptive",
        "number_of_questions": len(questions_for_user),
        "questions": questions_for_user
    })