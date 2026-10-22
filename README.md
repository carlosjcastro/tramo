# Tramo

Tramo compares the syllabus of a subject a student already passed with the syllabus of the subject they want recognized, and drafts a subject equivalence report for the reviewing professor.

Universities in Argentina and across Latin America resolve equivalences by hand, often over many months. Tramo gives the professor a structured starting point so the review focuses on judgment instead of reading two long documents side by side.

## How it works

1. Both syllabi are split into topics.
2. Every topic of the destination subject is compared by meaning against all topics of the origin subject using multilingual open source embeddings.
3. Each destination topic is labeled as covered, partial or no evidence, and the matching origin fragment is shown.
4. Coverage is computed with plain code, not by the model. Covered counts as 1, partial as 0.5.
5. The verdict follows the rule of the Facultad de Tecnología y Ciencias Aplicadas of UNCA: a partial equivalence is only proposed when equivalent content exceeds 50 percent of the analytic program, and the professor lists the topics still to be examined.

The tool never decides. The professor signs the report and the university council resolves.

## Privacy

Everything runs on open models. The default backend runs on CPU inside the container, and an Ollama backend is available so a faculty can host it on its own server and keep academic records inside the institution.

## Run locally

```
python -m venv .venv
pip install -r requirements_dev.txt
python -m pytest
python -m uvicorn app.api:app
```

Open http://localhost:8000. The first request downloads the embedding model.

To use Ollama instead:

```
set TRAMO_EMBEDDING_BACKEND=ollama
set TRAMO_EMBEDDING_MODEL=embeddinggemma
python -m uvicorn app.api:app
```

## Configuration

| Variable | Default |
| --- | --- |
| TRAMO_EMBEDDING_BACKEND | fastembed |
| TRAMO_EMBEDDING_MODEL | sentence-transformers/paraphrase-multilingual-mpnet-base-v2 |
| TRAMO_COVERED_THRESHOLD | 0.65 |
| TRAMO_PARTIAL_THRESHOLD | 0.5 |
| TRAMO_PARTIAL_RULE | 0.5 |
| TRAMO_MAX_CHARS | 8000 |

## Deploy

The repository contains a Dockerfile that serves the API and the web interface on port 7860, ready for Hugging Face Spaces (Docker SDK), Render or Railway.

## Project layout

```
app/domain.py       data models
app/syllabus.py     topic extraction
app/embedding.py    embedding backends
app/matching.py     semantic matching
app/policy.py       equivalence rule
app/service.py      orchestration
app/api.py          HTTP interface
app/static/         web interface
tests/              unit and API tests
```

## Status

This is a prototype. Thresholds are starting values and still need calibration against the official equivalence tables of real study plans. Sample syllabi in `samples/` are partly simulated.

## License

MIT
