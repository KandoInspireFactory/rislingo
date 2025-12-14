# TOEFL Speaking Master - Backend

FastAPI backend for TOEFL iBT Speaking Task 3 practice application.

## Setup

### Prerequisites

- Python 3.12+ (via Anaconda)
- PostgreSQL 15
- Anaconda environment `rislingo`

### Installation

**⚠️ IMPORTANT: Always use the `rislingo` Anaconda environment**

```bash
# Activate the rislingo environment
conda activate rislingo

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Database Setup

```bash
# Create database (if not already created)
createdb toefl_speaking_dev

# Run migrations
alembic upgrade head
```

### Running the Application

**⚠️ IMPORTANT: Run in the `rislingo` environment**

```bash
# Activate environment
conda activate rislingo

# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

API documentation: http://localhost:8000/docs

## Project Structure

```
backend/
├── alembic/              # Database migrations
├── models.py             # SQLAlchemy models
├── database.py           # Database configuration
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for GPT-4, Whisper, and TTS

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```
