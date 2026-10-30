from rag_citation import attach_question_citation, retrieve_with_citations


def test_attach_question_citation():
    question = {
        "id": 1,
        "subject": "Physics",
        "chapter": "Electrostatics",
        "question_text": "What is the SI unit of electric charge?",
        "solution": "The SI unit of charge is the coulomb.",
    }

    result = attach_question_citation(question)

    assert result["citations"][0]["source_type"] == "jee_question_bank"
    assert "Q1" in result["citations"][0]["title"]
    assert "coulomb" in result["citations"][0]["snippet"].lower()


def test_retrieve_with_citations_filters_and_adds_citation_metadata():
    questions = [
        {
            "id": 11,
            "subject": "Physics",
            "chapter": "Electricity",
            "question_text": "State Ohm's law.",
            "solution": "Voltage is directly proportional to current at constant temperature.",
        },
        {
            "id": 12,
            "subject": "Chemistry",
            "chapter": "Acids",
            "question_text": "What is the pH of pure water?",
            "solution": "Pure water has pH 7.",
        },
    ]

    result = retrieve_with_citations(questions, query="ohm law voltage current", subject="Physics", number=1)

    assert len(result) == 1
    assert result[0]["citations"][0]["subject"] == "Physics"
    assert result[0]["id"] == 11


if __name__ == "__main__":
    test_attach_question_citation()
    test_retrieve_with_citations_filters_and_adds_citation_metadata()
    print("rag citation tests passed")
