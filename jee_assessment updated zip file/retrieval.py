from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency fallback
    SentenceTransformer = None


_EMBEDDING_MODEL = None


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    return " ".join(value.split())


def _get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None and SentenceTransformer is not None:
        try:
            _EMBEDDING_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:  # pragma: no cover - model may not be downloadable in CI
            _EMBEDDING_MODEL = False
    return _EMBEDDING_MODEL


def _embedding_similarity(query: str, question: Dict[str, Any]) -> float:
    model = _get_embedding_model()
    if not model or model is False:
        return _token_overlap_score(query, question)

    try:
        query_embedding = model.encode(query, convert_to_tensor=False)
        text = " ".join([
            str(question.get("question_text") or ""),
            str(question.get("solution") or ""),
            str(question.get("chapter") or ""),
        ])
        doc_embedding = model.encode(text, convert_to_tensor=False)
        dot = sum(a * b for a, b in zip(query_embedding, doc_embedding))
        norm = (sum(a * a for a in query_embedding) ** 0.5) * (sum(b * b for b in doc_embedding) ** 0.5)
        if norm == 0:
            return 0.0
        return float(dot / norm)
    except Exception:  # pragma: no cover - just fallback
        return _token_overlap_score(query, question)


def _token_overlap_score(query: str, question: Dict[str, Any]) -> float:
    q_tokens = set(_normalize_text(query).split())
    if not q_tokens:
        return 0.0

    evidence = " ".join([
        str(question.get("question_text") or ""),
        str(question.get("solution") or ""),
        str(question.get("chapter") or ""),
    ])
    evidence_tokens = set(_normalize_text(evidence).split())
    if not evidence_tokens:
        return 0.0
    overlap = len(q_tokens & evidence_tokens)
    return overlap / max(len(q_tokens), 1)


def build_question_citation(question: Dict[str, Any]) -> Dict[str, Any]:
    subject = question.get("subject") or "Unknown"
    chapter = question.get("chapter") or "Unknown"
    question_id = question.get("id") or question.get("question_number") or "unknown"
    snippet = question.get("solution") or question.get("question_text") or ""
    snippet = snippet.strip()
    if len(snippet) > 220:
        snippet = snippet[:217].rstrip() + "..."

    return {
        "source_id": f"jee:{subject}:{chapter}:Q{question_id}",
        "source_type": "jee_question_bank",
        "title": f"{subject} • {chapter} • Q{question_id}",
        "snippet": snippet,
        "subject": subject,
        "chapter": chapter,
        "question_id": question_id,
    }


def attach_question_citation(question: Dict[str, Any]) -> Dict[str, Any]:
    question_copy = dict(question)
    question_copy["citations"] = [build_question_citation(question_copy)]
    return question_copy


def retrieve_with_citations(
    questions: Iterable[Dict[str, Any]],
    query: Optional[str] = None,
    subject: Optional[str] = None,
    chapter: Optional[str] = None,
    difficulty: Optional[str] = None,
    number: int = 5,
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []

    for question in questions:
        if subject and str(question.get("subject", "")).lower() != str(subject).lower():
            continue
        if chapter and str(question.get("chapter", "")).lower() != str(chapter).lower():
            continue
        if difficulty and str(question.get("difficulty", "")).lower() != str(difficulty).lower():
            continue
        filtered.append(question)

    if query:
        filtered = sorted(
            filtered,
            key=lambda q: _embedding_similarity(query, q),
            reverse=True,
        )

    result = []
    for question in filtered[:number]:
        result.append(attach_question_citation(question))
    return result


__all__ = [
    "build_question_citation",
    "attach_question_citation",
    "retrieve_with_citations",
]
