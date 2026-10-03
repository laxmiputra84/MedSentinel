# MedSentinel — Healthcare Intelligence & Insurance Platform

> **Full-stack enterprise healthcare architecture built with Next.js, FastAPI, MySQL (InnoDB with Connection Pooling), and JWT Authentication while preserving 100% of the MedSentinel frontend UI design, user flows, and features.**

---

## 🌟 Architecture & Technology Stack

- **Frontend**: Next.js 14 App Router, TypeScript, React, Tailwind CSS, Material Symbols.
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy ORM, Pydantic v2 Settings.
- **Database**: **MySQL 8.0 (InnoDB)** with connection pooling (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`).
- **Authentication**: JWT Access Token (60 min) + Refresh Token rotation (7 days) with Passlib bcrypt password hashing.
- **Database Driver**: `PyMySQL` (`mysql+pymysql://...`).
- **Migrations**: Alembic database migrations.

---

## 📁 Project Structure

```
MedSentinel/
├── backend/                       # Python FastAPI Backend
│   ├── app/
│   │   ├── core/                  # MySQL DB Engine, Config, Security (JWT, bcrypt)
│   │   ├── models/                # SQLAlchemy MySQL InnoDB models & indexes
│   │   ├── schemas/               # Pydantic v2 validation models
│   │   ├── routers/               # Modular FastAPI endpoints
│   │   ├── services/              # Business logic (Auth, OTP, Claims, Eligibility)
│   │   ├── dependencies/          # Role-Based Access Control (RBAC)
│   │   └── main.py                # FastAPI entrypoint with MySQL lifespan checks
│   ├── migrations/                # Alembic MySQL database migrations
│   ├── tests/                     # Pytest automated test suite
│   ├── seed_data.py               # MySQL idempotent seed script
│   └── requirements.txt
│
├── frontend/                      # Next.js 14 Frontend
│   ├── app/                       # 16 App Router pages
│   ├── components/                # Reusable UI components & notification bell
│   ├── lib/                       # API client with JWT refresh interceptors
│   └── package.json
│
└── docker-compose.yml             # MySQL 8.0 + FastAPI + Next.js orchestration
```

---

## 🚀 Getting Started

### Option 1: Docker Compose (Recommended)

Run the entire platform with a dedicated MySQL 8.0 container and persistent volume storage:

```bash
docker compose up --build
```

- **Frontend**: `http://localhost:3000`
- **Backend API & Swagger Docs**: `http://localhost:8000/docs`
- **MySQL Database Port**: `localhost:3306`

---

### Option 2: Local Development Setup

#### 1. MySQL Database Setup

1. Log into your MySQL server:
   ```bash
   mysql -u root -p
   ```
2. Create the MedSentinel databases:
   ```sql
   CREATE DATABASE medsentinel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE DATABASE medsentinel_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

#### 2. Backend Setup (FastAPI)

1. Open a terminal and navigate to `backend`:
   ```powershell
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Configure your `.env` file:
   ```env
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/medsentinel
   TEST_DATABASE_URL=mysql+pymysql://root:password@localhost:3306/medsentinel_test
   JWT_SECRET_KEY=medsentinel_super_secure_jwt_secret_key_change_in_production_2026
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```
5. Apply Alembic migrations or run database seeder:
   ```powershell
   alembic upgrade head
   python seed_data.py
   ```
6. Start the FastAPI server:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
   *FastAPI Swagger documentation will be available at `http://localhost:8000/docs`.*

#### 3. Frontend Setup (Next.js)

1. Open a new terminal and navigate to `frontend`:
   ```powershell
   cd frontend
   ```
2. Install packages:
   ```powershell
   npm install
   ```
3. Start the Next.js development server:
   ```powershell
   npm run dev
   ```
4. Access `http://localhost:3000` in your web browser.

---

## 🔑 Pre-Seeded Accounts

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **USER** | `demo@medsentinel.com` | `password123` | Patient services, booking, claims, vault |
| **HOSPITAL_ADMIN** | `hospitaladmin@medsentinel.com` | `hospital123` | Hospital statistics & appointment management |
| **INSURANCE_ADMIN** | `insuranceadmin@medsentinel.com` | `insurance123` | Claim reviews & status transitions |
| **SUPER_ADMIN** | `superadmin@medsentinel.com` | `admin123` | Global platform analytics & admin controls |

---

## 🧪 Running Automated Tests

Execute the backend test suite:

```powershell
python -m pytest backend/tests/test_api.py -v
```

---

## 🛡️ MySQL InnoDB Schema & Indexes

All tables are created with `ENGINE=InnoDB` and optimized indexes for high query performance:
- `users`: Indexed on `(email, role)`.
- `hospitals`: Indexed on `(location, specialization)`, `rating`, `distance`.
- `insurance_claims`: Indexed on `(user_id, claim_status)`, `(claim_status, claim_date)`.
- `claim_status_history`: Indexed on `(claim_id, created_at)`.
- `appointments`: Indexed on `(user_id, status)`, `(hospital_id, status)`, `(preferred_date, department)`.
- `notifications`: Indexed on `(user_id, is_read)`, `(user_id, created_at)`.
- `user_documents`: Indexed on `(user_id, status)`, `(user_id, doc_type)`.
