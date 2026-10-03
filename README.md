# JEE Assessment AI — RAG MVP

A reproducible MVP for a JEE question corpus, retrieval and ground-truth-first answer evaluation.

## What is implemented

1. PDF question extraction/parsing
2. Clean 25-question sample corpus
3. Answer-key and reference-solution storage
4. PostgreSQL/pgvector schema for Supabase
5. Supabase ingestion script
6. Local embedding generation using BGE-large-en-v1.5
7. Local semantic retrieval
8. Ground-truth-first answer evaluation
9. Streamlit evaluation demo
10. Automated tests

## Architecture

```text
JEE PDF
  ↓
Extraction + parsing
  ↓
questions_clean.json
  ↓
Validation
  ├──→ Supabase PostgreSQL
  │       ↓
  │     pgvector
  │       ↓
  │     Retrieval
  │
  └──→ Embedding model
          ↓
      Semantic search

Student answer
  ↓
Stored answer key + reference solution
  ↓
Correctness / score
  ↓
Feedback explanation
```

## Run locally

```bash
pip install -r requirements.txt
pytest -q
streamlit run app/app.py
```

For Supabase ingestion, create the tables using `database/schema.sql`, create a local `.env` from `.env.example`, then run:

```bash
python database/ingest.py
```

For embeddings:

```bash
python embeddings/build_embeddings.py
```

## Security

Never commit `.env`, passwords, raw PDFs, or restricted/commercial source material. The sample corpus should only be redistributed when its source/license permits it.
