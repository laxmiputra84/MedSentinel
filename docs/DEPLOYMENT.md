# MedSentinel — Production Deployment Guide

## 1. Prerequisites
- **Python**: 3.10+
- **Node.js**: 18.0+
- **Database**: MySQL 8.0+
- **Cache & Event Bus**: Redis 6.0+ (Optional; local in-memory fallback enabled automatically)
- **OCR Engine**: Tesseract OCR (`tesseract` on system PATH)

---

## 2. Environment Configuration (.env)

Create `backend/.env` with the following production keys:

```ini
# Application
PROJECT_NAME="MedSentinel"
ENVIRONMENT="production"
SECRET_KEY="<strong-cryptographic-random-secret>"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (MySQL 8.0)
DATABASE_URL="mysql+pymysql://medsentinel_user:medsentinel_pass@localhost:3306/medsentinel_db"

# Redis Event Bus (Optional - fallbacks to resilient memory queue if unavailable)
REDIS_URL="redis://localhost:6379/0"

# Embeddings & AI
EMBEDDING_PROVIDER="fastembed" # options: fastembed, gemini
GEMINI_API_KEY="<optional-for-cloud-reasoning>"
```

---

## 3. Backend Deployment

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations (or initial schema build)
python -c "from app.core.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"

# Start FastAPI production server with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 4. Frontend Deployment

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build production Next.js bundle
npm run build

# Start Next.js production server
npm run start -p 3000
```
