# Voice Technician Assistant Backend

Enterprise-grade FastAPI backend for an AI-powered Voice Technician Assistant. Field technicians can navigate their entire maintenance workflows (geolocating, finding nearby assets, creating/summarizing tickets) purely via natural speech or text.

## Tech Stack
* **Python**: 3.12
* **Framework**: FastAPI + Pydantic v2
* **Agent Engine**: LangGraph + Anthropic Claude (with offline tool selection fallbacks)
* **Speech-to-Text**: Strategy pattern interface supporting Whisper & Deepgram
* **Database**: PostgreSQL (with pgvector semantic search support) + SQLAlchemy 2.x
* **Cache & Memory**: Redis (session state + rate limiting)
* **Migrations**: Alembic

---

## Directory Layout
* `/app/api`: FastAPI HTTP & WebSocket controllers.
* `/app/core`: Configuration, logging, exception handlers, middlewares.
* `/app/database`: Database connection, SQLAlchemy models, Repository Pattern implementation.
* `/app/services`: High-level business logicians (Tickets, Assets, Memory, Speech Strategy).
* `/app/agents`: LangGraph state-graph workflow nodes and Claude tool bindings.
* `/app/schemas`: Pydantic validation request/response contracts.
* `/app/integrations`: Client integrations (Anthropic, Deepgram, Redis).
* `/tests`: Pytest suite (Unit & integration flows).

---

## Getting Started

### Local Setup
1. **Clone & Setup Environment**:
   ```bash
   cp .env.example .env
   # Add your API Keys (ANTHROPIC_API_KEY, DEEPGRAM_API_KEY, etc.)
   ```

2. **Docker Compose Launch**:
   Launch FastAPI backend, PostgreSQL + pgvector, and Redis containers:
   ```bash
   docker-compose up --build
   ```

3. **Running locally without Docker (SQLite & Memory Fallback)**:
   Ensure you set the local SQLite database URL in your `.env` file:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./voice_bot.db
   ```
   Rebuild your virtual environment and start the uvicorn server directly:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt # or install manually
   PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

   PYTHONPATH=. .venv/bin/python -m app.agents.livekit_agent dev
   ```

4. **Interactive Documentation**:
   Access the production-ready Swagger UI at:
   `http://localhost:8000/docs`


---

## Running Tests
Run tests locally using pytest:
```bash
poetry install
poetry run pytest -v
```
All external network interactions (OpenAI, Deepgram, Redis) are cleanly mocked in the test suite using in-memory databases and dictionary-backed session stores.

---

## Local Whisper Configuration

This application supports transcribing voice recordings using a locally-running Whisper speech-to-text service or the OpenAI Whisper Cloud API.

### Option A: Local Whisper CLI/Python Package
1. Ensure you have installed the Whisper package and its system dependencies (e.g., `ffmpeg`):
   ```bash
   pip install openai-whisper
   # On macOS using Homebrew:
   brew install ffmpeg
   ```
2. Configure your `.env` file to use `local` Whisper:
   ```env
   STT_PROVIDER=whisper
   WHISPER_MODE=local
   ```
3. The backend will automatically import `whisper` dynamically and run transcribing on a local threadpool. If the python package is not found, it will execute the `whisper` command in your terminal using a subprocess.

### Option B: Cloud Whisper API
1. Update your `.env` file with your OpenAI Whisper API credentials:
   ```env
   STT_PROVIDER=whisper
   WHISPER_MODE=cloud
   WHISPER_API_KEY=your_openai_api_key_here
   ```

