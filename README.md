# Autonomous Document Generation Agent

A FastAPI service that turns a natural-language request into an autonomous task plan,
executes the plan with Groq, quality-checks the result, and produces a formatted Word
document. The generated task list is returned in the API response so the agent's
decisions are visible and demo-friendly.

## How it works

```text
POST /agent
    -> Planner: infer document type, assumptions, sections, and dependencies
    -> Executor: write each planned section with prior-step context
    -> Reflection: deterministic checks + independent LLM review
    -> Recovery: one bounded revision pass when reflection fails
    -> Document tool: render and save DOCX
    -> JSON response: plan, review result, summary, and download URL
```

The mandatory engineering improvement is **reflection/self-check with recovery**.
Pure generation can produce incomplete or inconsistent documents. This workflow checks
length, structure, empty/duplicate sections, readability, request coverage, consistency,
and unsupported claims. A failed review triggers one revision and a second review; a
second failure returns a controlled error instead of silently publishing poor output.
Transient Groq failures also use bounded exponential-backoff retries.

## Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, set a free Groq API key, then run:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API. Health is available at
`GET /health`; generated documents can be downloaded from the `document_url` returned
by `POST /agent`.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"request":"Create a project proposal for an inventory management system for a mid-sized retail company."}'
```

## Required demo inputs

Standard business request:

```json
{
  "request": "Create a project proposal for an inventory management system for a mid-sized retail company. Include scope, timeline, budget categories, risks, and success metrics."
}
```

Complex request with missing and conflicting details:

```json
{
  "request": "Create a technical project plan for moving our 12-person support team from spreadsheets to a customer ticketing platform. Launch quickly but avoid operational disruption; no vendor, budget, deadline, or migration approach has been selected. Decide sensible assumptions, phases, responsibilities, risks, training, rollback, and measurable acceptance criteria."
}
```

The planner does not hide ambiguity: its assumptions appear in both the execution plan
and the generated document.

## Tests

Tests use a deterministic fake LLM, so they consume no API credits and verify planning,
orchestration, validation, DOCX creation, request guardrails, and document download.

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Architecture and tradeoff

The code keeps the important pieces easy to find: `app/routes.py` for the API,
`app/workflow.py` for orchestration, `app/agents/` for planner/executor/reflection,
and `app/tools/` for templates, validation, and DOCX rendering. A single orchestrated
workflow was chosen over a multi-agent framework: it is easy to explain and debug
within the assignment's 60-minute constraint, while the planner/executor/reviewer
boundaries remain replaceable. The tradeoff is less dynamic delegation in exchange for
predictable execution, lower latency, and simpler failure handling.

One useful debugging story for the video: Groq's OpenAI-compatible JSON mode accepts
`{"type":"json_object"}`, but not an arbitrary `schema` member. The schema is therefore
included in the prompt and validated again with Pydantic. This avoids API-level 400
errors while retaining strict application-side contracts.

## Project layout

```text
app/
  agents/        planner, executor, reflection
  routes.py      routes and DOCX download
  config/        environment settings
  core/          errors and structured logging
  llm/           async Groq client with retry
  workflow.py    planner, executor, reflection, recovery
  schemas/       Pydantic API/agent contracts
  tools/         templates, validation, DOCX formatting
templates/       proposal and requirements structures
tests/           credit-free workflow and API tests
output/          generated documents
```
