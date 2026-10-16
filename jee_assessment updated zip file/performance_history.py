import os
import json
from datetime import datetime

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "performance_history.json")

def _load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_all_history(records):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")


def create_performance_record(
    evaluation_result,
    time_taken_minutes
):
    """
    Create a performance-history record from an evaluation result.
    """
    history = _load_history()
    timestamp = datetime.now()

    record = {
        "test_id": len(history) + 1,
        "test_date": timestamp.strftime("%Y-%m-%d"),
        "timestamp": timestamp.isoformat(),
        "time_taken_minutes": time_taken_minutes,

        "total_questions": (
            evaluation_result["correct"]
            + evaluation_result["wrong"]
            + evaluation_result["unattempted"]
        ),

        "correct": evaluation_result["correct"],
        "wrong": evaluation_result["wrong"],
        "unattempted": evaluation_result["unattempted"],
        "marks": evaluation_result["marks"],
        "total_marks": evaluation_result["marks"],

        "subject_results": evaluation_result.get("subject_results", {}),
        "topic_feedback": evaluation_result.get("topic_feedback", {}),
        "strong_topics": evaluation_result.get("strong_topics", []),
        "average_topics": evaluation_result.get("average_topics", []),
        "weak_topics": evaluation_result.get("weak_topics", [])
    }

    return record


def save_performance_record(record):
    """
    Save a performance record persistently.
    """
    records = _load_history()
    records.append(record)
    _save_all_history(records)
    return record


def get_performance_history():
    """
    Return all stored performance records.
    """
    return _load_history()


def get_cumulative_topic_feedback():
    """
    Aggregate topic performance across all completed tests in history.
    """
    cumulative = {}
    for record in _load_history():
        tf = record.get("topic_feedback", {})
        for subject, topics in tf.items():
            if subject not in cumulative:
                cumulative[subject] = {}
            for topic, stats in topics.items():
                if topic not in cumulative[subject]:
                    cumulative[subject][topic] = {
                        "correct": 0,
                        "attempted": 0,
                        "unattempted": 0
                    }
                cumulative[subject][topic]["correct"] += stats.get("correct", 0)
                cumulative[subject][topic]["attempted"] += stats.get("attempted", 0)
                cumulative[subject][topic]["unattempted"] += stats.get("unattempted", 0)

    for subject, topics in cumulative.items():
        for topic, stats in topics.items():
            if stats["attempted"] == 0:
                stats["percentage"] = 0
                stats["performance"] = "Not Enough Data"
            else:
                pct = (stats["correct"] / stats["attempted"]) * 100
                stats["percentage"] = pct
                if pct >= 80:
                    stats["performance"] = "Strong"
                elif pct >= 50:
                    stats["performance"] = "Average"
                else:
                    stats["performance"] = "Needs Improvement"
    return cumulative