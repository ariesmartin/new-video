# AI Video Engine - Backend

AI-powered video generation engine with LangGraph orchestration.

## Tech Stack

- **Framework**: FastAPI
- **Agent Orchestration**: LangGraph
- **Database**: Supabase (PostgreSQL + pgvector)
- **Task Queue**: Celery + Redis
- **AI Models**: OpenAI, Anthropic, Google Gemini, DeepSeek

## Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Copy and configure environment
cp .env.template .env
# Edit .env with your settings

# Run development server
uvicorn backend.main:app --reload
```

## Project Structure

```
backend/
├── api/           # FastAPI routes
├── schemas/       # Pydantic models
├── services/      # Business logic
├── graph/         # LangGraph agents
├── tasks/         # Celery async tasks
└── supabase/      # Database migrations
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
