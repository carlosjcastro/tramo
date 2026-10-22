# Tramo

Tramo compares the analytic program of a subject a student already passed with the program of the subject they want recognized, and drafts an equivalence report for the reviewing professor.

Universities in Argentina and across Latin America resolve equivalences by hand, often over many months. Tramo gives the professor a structured starting point with the evidence laid out, so the review focuses on judgment instead of reading two long documents side by side.

## How it works

1. Both programs are loaded as text, PDF or Word (.docx) files.
2. A local Gemma model reads each program and extracts its teaching topics.
3. The model reads every destination topic against the full list of origin topics and labels it as covered, partial or no evidence. It cites the origin topics it relied on and writes a short reason.
4. Coverage is computed with plain code, not by the model. Covered counts as 1, partial as 0.5.
5. The verdict follows the rule of the Facultad de Tecnologia y Ciencias Aplicadas of UNCA: a partial equivalence is only proposed when equivalent content exceeds 50 percent of the analytic program, and the topics still to be taken are listed.
6. The model writes a short recommendation from the computed facts.
7. The professor can change the status of any topic. The numbers are recalculated in code and the AI recommendation is withdrawn.

The AI proposes and justifies. The professor signs the report and the university council resolves.

## Privacy

Everything runs locally with Ollama and an open weights model. Documents never leave the machine and nothing is stored.

## Run locally

```
python -m venv .venv
pip install -r requirements_dev.txt
ollama pull gemma4:e4b
python -m pytest
python -m uvicorn app.api:app
```

Open http://localhost:8000. A full analysis can take several minutes depending on the hardware. The first request also loads the model.

## Configuration

| Variable | Default |
| --- | --- |
| TRAMO_MODEL | gemma4:e4b |
| OLLAMA_HOST | http://localhost:11434 |
| TRAMO_NUM_CTX | 12288 |
| TRAMO_BATCH_SIZE | 12 |
| TRAMO_REQUEST_TIMEOUT | 600 |
| TRAMO_PARTIAL_RULE | 0.5 |
| TRAMO_MAX_CHARS | 20000 |
| TRAMO_MAX_FILE_BYTES | 5242880 |

## Project layout

```
app/domain.py       data models
app/errors.py       application errors
app/extraction.py   PDF and Word text extraction
app/noise.py        filter for headers, names and bibliography
app/syllabus.py     rule based topic splitting, used as fallback
app/llm.py          structured output client for Ollama
app/topics.py       topic extraction with the model
app/assessment.py   topic by topic reasoning with the model
app/advisor.py      written recommendation
app/policy.py       equivalence rule
app/service.py      orchestration
app/api.py          HTTP interface
app/static/         web interface
tests/              unit and API tests
```

## Status

Prototype. Prompts still need calibration against real study plans and the official equivalence tables. Sample programs in `samples/` are partly simulated.

## License

MIT
