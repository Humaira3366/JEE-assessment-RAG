from validation import validate_question


bad_question = {
    "question": "",
    "options": ["Volt", "Ampere", "Ampere"],
    "correct_answer": "Ohm",
    "subject": "Physics",
    "chapter": "",
    "topic": "Electric Current",
    "difficulty": "Easy"
}

valid, errors = validate_question(bad_question)

print("Valid:", valid)
print("Errors:")

for error in errors:
    print("-", error)