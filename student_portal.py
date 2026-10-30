from rest_framework.decorators import api_view
from rest_framework.response import Response

from retrieval import load_questions, retrieve_questions, retrieve_questions_with_citations
from validation import validate_question
from evaluation import evaluate_selected_questions
from assessment_generator import generate_assessment
from adaptive import select_adaptive_questions
from rag_citation import attach_question_citation

from performance_history import (
    create_performance_record,
    save_performance_record,
    get_performance_history,
    get_cumulative_topic_feedback
)


def _with_citations(question_or_questions):
    if isinstance(question_or_questions, list):
        return [attach_question_citation(q) for q in question_or_questions]
    return attach_question_citation(question_or_questions)


@api_view(["GET"])
def get_questions(request):

    questions = load_questions()

    subject = request.GET.get("subject")
    chapter = request.GET.get("chapter")
    difficulty = request.GET.get("difficulty")
    number = int(request.GET.get("number", 5))
    query = request.GET.get("query")

    results = retrieve_questions_with_citations(
        questions,
        query=query,
        subject=subject,
        chapter=chapter,
        difficulty=difficulty,
        number=number,
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
        if "citations" not in question_copy:
            question_copy["citations"] = [
                {
                    "source_id": f"jee:{question_copy.get('subject', 'Unknown')}:{question_copy.get('chapter', 'Unknown')}:Q{question_copy.get('id')}",
                    "source_type": "jee_question_bank",
                    "title": f"{question_copy.get('subject', 'Unknown')} • {question_copy.get('chapter', 'Unknown')} • Q{question_copy.get('id')}",
                    "snippet": question_copy.get("solution") or question_copy.get("question_text") or "",
                }
            ]

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

    result["questions"] = _with_citations(result.get("questions", []))
    result["citations_enabled"] = True
    result["citation_source"] = "jee_question_bank"

    return Response(result)


@api_view(["POST"])
def generate_adaptive_test(request):

    questions = load_questions()

    topic_feedback = request.data.get("topic_feedback")
    use_cumulative = request.data.get("cumulative", False)

    if not topic_feedback or use_cumulative:
        topic_feedback = get_cumulative_topic_feedback()

    number = int(request.data.get("number", 10))

    previous_question_ids = request.data.get("previous_question_ids", [])
    if not previous_question_ids:
        for rec in get_performance_history():
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
        question_copy.pop("correct_answer", None)
        question_copy["citations"] = [
            {
                "source_id": f"jee:{question_copy.get('subject', 'Unknown')}:{question_copy.get('chapter', 'Unknown')}:Q{question_copy.get('id')}",
                "source_type": "jee_question_bank",
                "title": f"{question_copy.get('subject', 'Unknown')} • {question_copy.get('chapter', 'Unknown')} • Q{question_copy.get('id')}",
                "snippet": question_copy.get("solution") or question_copy.get("question_text") or "",
            }
        ]

        questions_for_user.append(question_copy)

    return Response({
        "subject": "Adaptive Assessment",
        "type": "adaptive",
        "number_of_questions": len(questions_for_user),
        "questions": questions_for_user,
        "citations_enabled": True,
        "citation_source": "jee_question_bank",
    })


