
# Full-Stack AI Chat Application

A full-stack AI chat application built with FastAPI, PostgreSQL, SQLAlchemy, and a browser-based frontend. It supports persistent conversations, API-key authentication, streaming AI responses, conversation isolation, rate limiting, and token usage tracking.

The application uses a local Ollama model through an OpenAI-compatible API, so it can run without paid OpenAI API access.

## Features

- Create, list, open, and delete chat sessions.
- PostgreSQL persistence for conversations and messages.
- API-key authentication.
- Session ownership and conversation isolation.
- Streaming AI responses using Server-Sent Events (SSE).
- Local LLM integration using Ollama and Qwen.
- Sliding-window conversation context management.
- Database-backed rolling rate limiting.
- HTTP 429 responses with Retry-After information.
- Token usage and estimated cost tracking.
- Responsive HTML, CSS, and JavaScript frontend.
- Automated tests using pytest and mocked AI responses.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database Driver | asyncpg |
| AI Integration | OpenAI Python SDK |
| Local AI Runtime | Ollama |
| AI Model | Qwen 2.5 1.5B |
| Frontend | HTML, CSS, JavaScript |
| Streaming | Server-Sent Events |
| Testing | pytest, pytest-asyncio, pytest-cov |

## Architecture

```text
Browser Frontend
      |
      | HTTP / SSE
      v
   FastAPI
      |
      +------ API Authentication
      |
      +------ Session Management
      |
      +------ Chat Service
      |          |
      |          +---- Conversation History
      |          |
      |          +---- Rate Limiting
      |          |
      |          +---- Ollama / Qwen
      |
      v
 SQLAlchemy
      |
      v
 PostgreSQL
```

## Prerequisites

Install the following before running the application:

- Python
- PostgreSQL
- Ollama
- Git

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/ajayharrieshtYT260949/full-stack-ai-chat-app.git
cd full-stack-ai-chat-app
```

If you already have the project locally, open its directory instead.

### 2. Create a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Make sure PostgreSQL is running.

Create a database named:

```text
chat_app_db
```

The application connects using the `DATABASE_URL` setting in `.env`.

Example:

```text
postgresql+asyncpg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/chat_app_db
```

Replace the example password with your own PostgreSQL password.

### 5. Configure Ollama

Install Ollama and download the model:

```powershell
ollama pull qwen2.5:1.5b
```

Check that the model is available:

```powershell
ollama list
```

Make sure the Ollama service is running before starting the application.

### 6. Configure environment variables

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure your PostgreSQL credentials and application API key.

The local Ollama configuration is:

```dotenv
OPENAI_API_KEY=ollama
OPENAI_MODEL=qwen2.5:1.5b
OPENAI_BASE_URL=http://localhost:11434/v1
```

`OPENAI_API_KEY=ollama` is a compatibility value for the OpenAI SDK. It is not a paid OpenAI API key.

Never commit your `.env` file.

## Run the Application

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload
```

Open the application:

| Resource | URL |
|---|---|
| Frontend | http://127.0.0.1:8000/ |
| Swagger API Documentation | http://127.0.0.1:8000/docs |
| Health Check | http://127.0.0.1:8000/health |

Database tables are created automatically when the application starts.

## API Endpoints

All session and chat endpoints require the `X-API-Key` header.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Create a chat session |
| GET | `/sessions` | List the user's sessions |
| GET | `/sessions/{id}/messages` | Retrieve conversation history |
| DELETE | `/sessions/{id}` | Delete a session and its messages |
| POST | `/sessions/{id}/chat` | Send a message and stream the AI response |

### Streaming

The chat endpoint uses Server-Sent Events (SSE).

The frontend receives streaming events such as:

- `token` — incremental assistant response content.
- `done` — completion and usage information.
- `error` — an error encountered during generation.

## Rate Limiting

The default configuration allows 20 accepted user messages per API key within a rolling one-hour window.

Further requests receive HTTP 429 with a `Retry-After` header.

The limits can be configured through environment variables.

## Conversation Memory

Conversation history is stored in PostgreSQL.

Before sending a prompt to the language model, the application loads the session's history and applies a sliding-window limit.

Older messages remain stored in the database; only the context sent to the model is trimmed.

Different sessions maintain separate conversation histories.

## Token Usage and Cost Tracking

The application tracks:

- Prompt tokens
- Completion tokens
- Estimated cost per session

Provider-reported token usage is preferred when available. If unavailable, token counts are estimated from text length.

Cost is calculated using the configured input and output pricing values.

For local Ollama usage, the example configuration uses zero provider-token pricing. These estimates are not a record of actual billing.

## Diagnostic Scripts

Optional scripts are available to verify external dependencies:

```powershell
python check_db.py
```

Checks the PostgreSQL connection.

```powershell
python check_local_ai.py
```

Checks the local Ollama model connection.

## Automated Tests

Run the test suite:

```powershell
pytest -v
```

Run tests with coverage:

```powershell
pytest --cov=app --cov-report=term-missing
```

The automated tests use an isolated SQLite test database and mocked AI streaming responses. They do not require paid AI API calls.

## Security Considerations

- API-key authentication protects session and chat routes.
- Session ownership is checked using a hashed API key.
- Environment variables are used for local secrets and configuration.
- `.env` is excluded from Git.
- The frontend stores the application API key in browser local storage for this assessment demonstration.

For production deployment, use individual user authentication, HTTPS, secure credential management, database migrations, and concurrency-safe rate limiting.

## Future Improvements

- User registration and login.
- Multiple AI model support.
- Conversation search.
- Export conversation history.
- Improved monitoring and logging.
- Production deployment.

## Demo Checklist

1. Create a new chat session.
2. Send a message and demonstrate streamed AI responses.
3. Show token usage and estimated cost.
4. Reload a previous conversation.
5. Create another session and demonstrate conversation isolation.
6. Delete a conversation.
7. Demonstrate rate limiting.
8. Run the automated test suite.
