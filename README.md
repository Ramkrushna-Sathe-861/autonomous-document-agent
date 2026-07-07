# Autonomous Document Generation Agent

An AI-powered autonomous document generation system built with **Python**, **FastAPI**, and **Groq LLM**.

The application accepts a natural language request, creates an execution plan, generates professional business content, validates the output, and produces a Microsoft Word document.

---

## Features

- Autonomous task planning
- Multi-step execution workflow
- AI-powered content generation using Groq
- Word document generation (.docx)
- Reflection and validation before final output
- REST API using FastAPI
- Modular and scalable architecture

---

## Tech Stack

- Python 3.12
- FastAPI
- Groq API
- python-docx
- Pydantic
- Uvicorn
- python-dotenv

---

## Project Structure

```
app/
├── api/
├── agents/
├── config/
├── core/
├── llm/
├── orchestrator/
├── schemas/
├── services/
├── tools/
└── main.py

output/
templates/
tests/
```

---

## Workflow

```
User Request
      │
      ▼
Planner Agent
      │
      ▼
Executor Agent
      │
      ▼
Document Tool
      │
      ▼
Reflection Agent
      │
      ▼
Generated Word Document
```

---

## API Endpoint

### POST `/agent`

Request

```json
{
  "request": "Create a project proposal for an Inventory Management System."
}
```

Response

```json
{
  "status": "completed",
  "summary": "Document generated successfully.",
  "document_path": "output/proposal.docx"
}
```

---

## Getting Started

### Clone Repository

```bash
git clone <repository-url>
cd autonomous-document-agent
```

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Environment

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file.

```env
GROQ_API_KEY=your_groq_api_key
MODEL_NAME=llama-3.3-70b-versatile
```

### Run the Application

```bash
uvicorn app.main:app --reload
```

---

## Future Enhancements

- Conversation memory
- Template selection
- Multiple document formats
- RAG integration
- Tool calling
- Persistent storage

---

## Author

**Ramkrushna Sathe**
