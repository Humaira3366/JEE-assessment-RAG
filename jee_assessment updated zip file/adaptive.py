def get_topic_priorities(topic_feedback):
    """
    Decide how important each topic is for the next assessment.
    """

    topic_priorities = {}

    for subject, topics in topic_feedback.items():

        topic_priorities[subject] = {}

        for topic, result in topics.items():

            performance = result["performance"]

            if performance == "Needs Improvement":
                priority = "High"

            elif performance == "Average":
                priority = "Medium"

            elif performance == "Strong":
                priority = "Low"

            else:
                priority = "Normal"

            topic_priorities[subject][topic] = priority

    return topic_priorities


def get_adaptive_topics(topic_feedback):
    """
    Return topics that should be prioritised in the next assessment.
    """

    topic_priorities = get_topic_priorities(
        topic_feedback
    )

    adaptive_topics = []

    for subject, topics in topic_priorities.items():

        for topic, priority in topics.items():

            if priority in ["High", "Medium"]:

                adaptive_topics.append({
                    "subject": subject,
                    "topic": topic,
                    "priority": priority
                })

    return adaptive_topics


def calculate_question_allocation(
    adaptive_topics,
    number
):
    """
    Decide how many questions each adaptive topic should receive.
    """

    high_priority = [
        topic
        for topic in adaptive_topics
        if topic["priority"] == "High"
    ]

    medium_priority = [
        topic
        for topic in adaptive_topics
        if topic["priority"] == "Medium"
    ]

    allocation = []

    remaining_questions = number

    # If both high and medium exist: 60% to high, 40% to medium
    # If only high exists: 100% to high
    # If only medium exists: 100% to medium
    if high_priority and not medium_priority:
        high_count = remaining_questions
    elif high_priority and medium_priority:
        high_count = max(1, round(number * 0.6))
        high_count = min(high_count, remaining_questions)
    else:
        high_count = 0

    if high_count > 0 and high_priority:
        base_questions = high_count // len(high_priority)
        remainder = high_count % len(high_priority)

        for index, topic in enumerate(high_priority):
            questions_for_topic = base_questions
            if index < remainder:
                questions_for_topic += 1

            allocation.append({
                "subject": topic["subject"],
                "topic": topic["topic"],
                "priority": "High",
                "questions": questions_for_topic
            })

        remaining_questions -= high_count

    # Give remaining questions to average topics (or any remaining quota)
    if medium_priority and remaining_questions > 0:
        base_questions = remaining_questions // len(medium_priority)
        remainder = remaining_questions % len(medium_priority)

        for index, topic in enumerate(medium_priority):
            questions_for_topic = base_questions
            if index < remainder:
                questions_for_topic += 1

            allocation.append({
                "subject": topic["subject"],
                "topic": topic["topic"],
                "priority": "Medium",
                "questions": questions_for_topic
            })

    return allocation


def select_adaptive_questions(
    questions,
    topic_feedback,
    number=5,
    previous_question_ids=None
):
    """
    Select questions according to adaptive priorities
    while avoiding previously attempted questions.
    """

    if previous_question_ids is None:
        previous_question_ids = []

    adaptive_topics = get_adaptive_topics(
        topic_feedback
    )

    allocation = calculate_question_allocation(
        adaptive_topics,
        number
    )

    selected_questions = []

    for item in allocation:

        matching_questions = []

        for question in questions:

            # Skip previously attempted questions
            if question["id"] in previous_question_ids:
                continue

            if question.get("subject") != item["subject"]:
                continue

            if question.get("chapter") != item["topic"]:
                continue

            try:
                from validation import validate_question
                valid, _ = validate_question(question)
                if not valid:
                    continue
            except Exception:
                pass

            matching_questions.append(question)

        required_questions = item["questions"]

        for question in matching_questions:

            if len(selected_questions) >= number:
                break

            if required_questions <= 0:
                break

            if question not in selected_questions:

                selected_questions.append(question)

                required_questions -= 1

    return selected_questions