# TOEFL Speaking Master

TOEFL iBT Speaking Task 3 (Academic Integrated) practice application with AI scoring and flashcard functionality.

## Project Overview

This application helps TOEFL test-takers practice Speaking Task 3 with:
- Automatic problem generation (Reading, Lecture, Question)
- Real-time recording and transcription
- AI-powered scoring based on TOEFL criteria
- Model answers with highlighted phrases
- Flashcard system for phrase memorization

## Tech Stack

### Frontend
- Next.js 15.5.7
- React 19.1.2
- TypeScript
- Tailwind CSS 3.x

### Backend
- FastAPI
- Python 3.12+ (Anaconda environment: `rislingo`)
- PostgreSQL 15
- SQLAlchemy + Alembic
- OpenAI API (GPT-4, Whisper, TTS)

## Setup Instructions

### 1. Database Setup

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database
createdb toefl_speaking_dev
```

### 2. Backend Setup

**⚠️ IMPORTANT: Always use the `rislingo` Anaconda environment**

```bash
cd backend

# Activate rislingo environment
conda activate rislingo

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
# .env.local is already created with NEXT_PUBLIC_API_URL

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── alembic/         # Database migrations
│   ├── models.py        # SQLAlchemy models
│   ├── database.py      # Database configuration
│   ├── main.py          # FastAPI application
│   └── .env             # Environment variables
│
├── frontend/            # Next.js frontend
│   ├── app/            # App Router pages
│   ├── public/         # Static assets
│   └── .env.local      # Frontend environment variables
│
└── .kiro/              # Kiro specs
    └── specs/
        └── toefl-speaking-app/
            ├── requirements.md
            ├── design.md
            └── tasks.md
```

## Development Workflow

1. Backend runs on port 8000 (in `rislingo` environment)
2. Frontend runs on port 3000
3. Database: PostgreSQL on port 5432

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://localhost:5432/toefl_speaking_dev
OPENAI_API_KEY=your_openai_api_key_here
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

### Backend
```bash
conda activate rislingo
pytest
```

### Frontend
```bash
npm test
```

## License

MIT
