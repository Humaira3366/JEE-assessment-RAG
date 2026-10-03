import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "raw_extracted.txt"
OUTPUT_FILE = BASE_DIR / "questions_clean.json"

MAX_QUESTIONS = 25
SECTION_RANGES = {"A": range(1, 11), "B": range(11, 26)}


def clean_page_separators(text: str) -> str:
    return re.sub(r"={5,}\s*PAGE\s+\d+\s*={5,}", "\n", text, flags=re.I)


def get_section(qno: int):
    for section, numbers in SECTION_RANGES.items():
        if qno in numbers:
            return section
    return None


def detect_subject(text: str):
    for subject in ("Mathematics", "Physics", "Chemistry"):
        if re.search(rf"\b{subject}\b", text, re.I):
            return subject
    return None


def clean_question_lines(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^PAGE\s+\d+$", line, re.I):
            continue
        if "JEE Main Mathematics Sample Paper" in line:
            continue
        if "JEE Main Physics Sample Paper" in line:
            continue
        if "JEE Main Chemistry Sample Paper" in line:
            continue
        cleaned.append(line)
    return cleaned


def parse_options_and_text(block: str):
    lines = clean_question_lines(block.splitlines())
    options = {}
    question_lines = []

    # Handles the current extraction format: A. (A) value, etc.
    option_pattern = re.compile(r"^([A-D])\.\s*\(\1\)\s*(.*)$", re.I)

    for line in lines:
        match = option_pattern.match(line)
        if match:
            options[match.group(1).upper()] = match.group(2).strip()
        else:
            question_lines.append(line)

    question_text = " ".join(question_lines)
    question_text = re.sub(r"\bV\s+alue\b", "Value", question_text)
    question_text = re.sub(r"\s+", " ", question_text).strip()
    return question_text, options


def parse_answer_section(text: str):
    marker = re.search(r"Answer Key & Detailed Explanation", text, re.I)
    if not marker:
        return {}

    answer_text = text[marker.end():]
    # Stop at nothing deliberately: answer section is the source of truth for q1..q25.
    pattern = re.compile(r"(?m)^\s*(\d{1,2})\.\s*\[([^\]]+)\]\s*(.*?)(?=^\s*\d{1,2}\.\s*\[|\Z)", re.S)
    answers = {}
    for m in pattern.finditer(answer_text):
        qno = int(m.group(1))
        if not 1 <= qno <= MAX_QUESTIONS:
            continue
        answer = m.group(2).strip()
        solution = re.sub(r"\s+", " ", m.group(3)).strip()
        answers[qno] = {"answer": answer, "solution": solution or None}
    return answers


def parse_questions(text: str):
    text = clean_page_separators(text)
    subject = detect_subject(text)

    # Only parse the question-paper portion. This is the key fix: answer-key numbers
    # must never be interpreted as new questions.
    question_part = re.split(r"Answer Key & Detailed Explanation", text, maxsplit=1, flags=re.I)[0]

    question_pattern = re.compile(r"(?m)^\s*(\d{1,2})\.\s+")
    matches = list(question_pattern.finditer(question_part))
    questions_by_number = {}

    for i, match in enumerate(matches):
        qno = int(match.group(1))
        if not 1 <= qno <= MAX_QUESTIONS or qno in questions_by_number:
            continue

        end = matches[i + 1].start() if i + 1 < len(matches) else len(question_part)
        block = question_part[match.end():end]
        question_text, options = parse_options_and_text(block)

        question_type = "mcq_single" if len(options) == 4 else ("mcq_partial" if options else "numerical")
        questions_by_number[qno] = {
            "question_number": qno,
            "subject": subject,
            "section": get_section(qno),
            "question_type": question_type,
            "question_text": question_text,
            "options": options,
            "answer": None,
            "solution": None,
        }

    return [questions_by_number[n] for n in sorted(questions_by_number)]


def main():
    text = INPUT_FILE.read_text(encoding="utf-8")
    questions = parse_questions(text)
    answers = parse_answer_section(text)

    for q in questions:
        key = answers.get(q["question_number"])
        if key:
            q["answer"] = key["answer"]
            q["solution"] = key["solution"]

    missing = [q["question_number"] for q in questions if not q["answer"]]

    OUTPUT_FILE.write_text(
        json.dumps(questions, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n===================================")
    print("QUESTION PARSING COMPLETE")
    print("===================================")
    print(f"Questions detected : {len(questions)}")
    print(f"Answer keys found  : {len(answers)}")
    print(f"Missing answers    : {missing or 'None'}")
    print(f"MCQ (4 options)    : {sum(len(q['options']) == 4 for q in questions)}")
    print(f"Partial options    : {sum(0 < len(q['options']) < 4 for q in questions)}")
    print(f"Numerical          : {sum(q['question_type'] == 'numerical' for q in questions)}")
    print(f"Output             : {OUTPUT_FILE}")

    print("\nFIRST 3 QUESTIONS")
    for q in questions[:3]:
        print(f"Q{q['question_number']} | {q['question_type']} | answer={q['answer']}")


if __name__ == "__main__":
    main()
