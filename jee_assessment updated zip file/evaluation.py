import json


def evaluate_selected_questions(all_questions, question_ids, student_answers):
    selected_questions = [
        question
        for question in all_questions
        if question["id"] in question_ids
    ]

    return evaluate_test(
        selected_questions,
        student_answers
    )


from retrieval import load_questions


# Main evaluation function
def evaluate_test(questions, student_answers):

    # --------------------------------------------------
    # 1. OVERALL EVALUATION
    # --------------------------------------------------

    correct = 0
    wrong = 0
    unattempted = 0

    for question in questions:

        question_id = question["id"]
        correct_answer = question["correct_answer"]

        if question_id not in student_answers:
            unattempted += 1

        elif student_answers[question_id] == correct_answer:
            correct += 1

        else:
            wrong += 1

    # Calculate final marks
    marks = (correct * 4) - (wrong * 1)


    # --------------------------------------------------
    # 2. SUBJECT-WISE EVALUATION
    # --------------------------------------------------

    subject_results = {}

    for question in questions:

        subject = question["subject"]
        question_id = question["id"]
        correct_answer = question["correct_answer"]

        if subject not in subject_results:
            subject_results[subject] = {
                "total": 0,
                "attempted": 0,
                "correct": 0,
                "wrong": 0,
                "unattempted": 0,
                "marks": 0
            }

        subject_results[subject]["total"] += 1

        if question_id not in student_answers:

            subject_results[subject]["unattempted"] += 1

        else:

            subject_results[subject]["attempted"] += 1

            if student_answers[question_id] == correct_answer:

                subject_results[subject]["correct"] += 1
                subject_results[subject]["marks"] += 4

            else:

                subject_results[subject]["wrong"] += 1
                subject_results[subject]["marks"] -= 1


    # --------------------------------------------------
    # 3. TOPIC-WISE EVALUATION
    # --------------------------------------------------

    topic_results = {}

    for question in questions:

        subject = question["subject"]
        topic = question.get("chapter", "Unknown")
        question_id = question["id"]
        correct_answer = question["correct_answer"]

        if subject not in topic_results:
            topic_results[subject] = {}

        if topic not in topic_results[subject]:

            topic_results[subject][topic] = {
                "total": 0,
                "attempted": 0,
                "correct": 0,
                "wrong": 0,
                "unattempted": 0
            }

        topic_results[subject][topic]["total"] += 1

        if question_id not in student_answers:

            topic_results[subject][topic]["unattempted"] += 1

        else:

            topic_results[subject][topic]["attempted"] += 1

            if student_answers[question_id] == correct_answer:

                topic_results[subject][topic]["correct"] += 1

            else:

                topic_results[subject][topic]["wrong"] += 1


    # --------------------------------------------------
    # 4. TOPIC PERFORMANCE + FEEDBACK
    # --------------------------------------------------

    strong_topics = []
    average_topics = []
    weak_topics = []
    not_enough_data = []

    topic_feedback = {}

    for subject, topics in topic_results.items():

        topic_feedback[subject] = {}

        for topic, result in topics.items():

            if result["attempted"] == 0:

                performance = "Not Enough Data"
                percentage = 0
                not_enough_data.append(topic)

            else:

                percentage = (
                    result["correct"] / result["attempted"]
                ) * 100

                if percentage >= 80:

                    performance = "Strong"
                    strong_topics.append(topic)

                elif percentage >= 50:

                    performance = "Average"
                    average_topics.append(topic)

                else:

                    performance = "Needs Improvement"
                    weak_topics.append(topic)

            topic_feedback[subject][topic] = {
                "correct": result["correct"],
                "attempted": result["attempted"],
                "unattempted": result["unattempted"],
                "percentage": percentage,
                "performance": performance
            }


    # --------------------------------------------------
    # 5. RETURN ALL RESULTS
    # --------------------------------------------------

    return {
        "correct": correct,
        "wrong": wrong,
        "unattempted": unattempted,
        "marks": marks,
        "subject_results": subject_results,
        "topic_feedback": topic_feedback,
        "strong_topics": strong_topics,
        "average_topics": average_topics,
        "weak_topics": weak_topics,
        "not_enough_data": not_enough_data
    }


# --------------------------------------------------
# TEST THE FUNCTION
# --------------------------------------------------

if __name__ == "__main__":

    questions = load_questions()

    # Temporary student answers for testing
    student_answers = {
    1: "Ampere",        # Correct
    2: "V = IR",        # Correct
    3: "Wrong Answer",  # Wrong
    4: "Joule",         # Wrong
    5: "[LT⁻¹]",       # Correct
    6: "Length of pendulum",  # Correct
    7: "2x",            # Correct
    8: "0",             # Wrong
    9: "3",             # Correct
    10: "1/2",          # Correct
    11: "Wrong Answer", # Wrong
    12: "5",            # Correct
    13: "6",            # Correct
    14: "H₂O",          # Correct
    15: "5"             # Wrong
}

    result = evaluate_test(
        questions,
        student_answers
    )

    print("Questions loaded:", len(questions))
    print("Student answers:", student_answers)

    print("\n--- Evaluation Result ---")
    print("Correct:", result["correct"])
    print("Wrong:", result["wrong"])
    print("Unattempted:", result["unattempted"])
    print("Final Score:", result["marks"])


    print("\n--- Subject-wise Performance ---")

    for subject, data in result["subject_results"].items():

        if data["attempted"] == 0:
            accuracy = 0
        else:
            accuracy = (
                data["correct"] / data["attempted"]
            ) * 100

        print("\n" + subject)
        print("Total Questions:", data["total"])
        print("Attempted:", data["attempted"])
        print("Correct:", data["correct"])
        print("Wrong:", data["wrong"])
        print("Unattempted:", data["unattempted"])
        print("Marks:", data["marks"])
        print(f"Accuracy: {accuracy:.1f}%")


    print("\n--- Topic Feedback ---")

    for subject, topics in result["topic_feedback"].items():

        print("\n" + subject)

        for topic, data in topics.items():

            if data["attempted"] == 0:

                print(
                    f"{topic} → "
                    f"Not Attempted → "
                    f"{data['performance']}"
                )

            else:

                print(
                    f"{topic} → "
                    f"{data['correct']}/{data['attempted']} correct "
                    f"({data['percentage']:.1f}%) → "
                    f"{data['performance']}"
                )


    print("\n--- Overall Feedback Summary ---")
    print("Strong Topics:", result["strong_topics"])
    print("Average Topics:", result["average_topics"])
    print(
        "Topics Needing Improvement:",
        result["weak_topics"]
    )
    print("Not Enough Data:", result["not_enough_data"])