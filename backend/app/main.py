import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine

import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify MySQL connectivity on startup & ensure schema is up to date
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connected to MySQL successfully on startup.")
        import app.models
        from app.core.database import Base, sync_database_schema
        sync_database_schema(engine, Base)
        print("Database schema verified and synced successfully.")
    except Exception as e:
        print(f"Warning: MySQL database connectivity check: {e}")

    # Hydrate VectorStore from MySQL / disk
    try:
        from app.core.database import SessionLocal
        from app.rag.vector_store import VectorStore
        with SessionLocal() as db_session:
            v_count = await VectorStore.hydrate_from_db(db_session)
            print(f"Vector Store indexed {v_count} points successfully on startup.")
    except Exception as e:
        print(f"Vector store startup hydration note: {e}")

    # Start Event-Driven Agent EventBus Background Worker
    try:
        from app.services.event_bus import event_bus
        event_bus.start()
        print("Event-Driven Agent EventBus worker started successfully.")
    except Exception as e:
        print(f"EventBus startup note: {e}")

    try:
        yield
    except (asyncio.CancelledError, GeneratorExit):
        pass
    finally:
        try:
            from app.services.event_bus import event_bus
            event_bus.stop()
        except Exception:
            pass

# Import all user routers
from app.routers import (
    auth,
    users,
    hospitals,
    saved_items,
    schemes,
    eligibility,
    insurances,
    claims,
    appointments,
    documents,
    notifications,
    analytics,
    ai_chat,
    health,
    recommendations,
    otp,
    agent_workflow,
    plugins,
    webhooks,
    events,
    human_review,
    patient_360,
    healthcare_analytics,
    agent_monitor,
)

# Import admin routers
from app.routers.admin import (
    dashboard as admin_dashboard,
    users as admin_users,
    hospitals as admin_hospitals,
    claims as admin_claims,
    documents as admin_documents,
    appointments as admin_appointments,
    insurances as admin_insurances,
    schemes as admin_schemes,
    notifications as admin_notifications,
    analytics as admin_analytics,
    ai_insights as admin_ai_insights,
    audit_logs as admin_audit_logs,
    knowledge_base as admin_knowledge_base,
    hospital_media as admin_hospital_media,
    ai_monitoring as admin_ai_monitoring,
    rag_debug as admin_rag_debug,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="MedSentinel Healthcare Platform API powered by MySQL, Private RAG AI, RBAC, and Enterprise Super Admin Dashboard.",
    version="2.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists and mount static files
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register User & Feature API Routers under /api
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(hospitals.router, prefix=settings.API_PREFIX)
app.include_router(saved_items.router, prefix=settings.API_PREFIX)
app.include_router(schemes.router, prefix=settings.API_PREFIX)
app.include_router(eligibility.router, prefix=settings.API_PREFIX)
app.include_router(insurances.router, prefix=settings.API_PREFIX)
app.include_router(claims.router, prefix=settings.API_PREFIX)
app.include_router(appointments.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)
app.include_router(analytics.router, prefix=settings.API_PREFIX)
app.include_router(ai_chat.router, prefix=settings.API_PREFIX)
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(recommendations.router, prefix=settings.API_PREFIX)
app.include_router(otp.router, prefix=settings.API_PREFIX)
app.include_router(agent_workflow.router, prefix=settings.API_PREFIX)
app.include_router(events.router, prefix=settings.API_PREFIX)
app.include_router(human_review.router, prefix=settings.API_PREFIX)
app.include_router(patient_360.router, prefix=settings.API_PREFIX)
app.include_router(healthcare_analytics.router, prefix=settings.API_PREFIX)
app.include_router(agent_monitor.router, prefix=settings.API_PREFIX)
app.include_router(plugins.router)
app.include_router(plugins.router, prefix=settings.API_PREFIX)
app.include_router(plugins.direct_router)
app.include_router(webhooks.router)

# Also mount documents, health, recommendations, otp, agent_workflow, and events at root to support direct non-prefixed calls
app.include_router(documents.router)
app.include_router(health.router)
app.include_router(recommendations.router)
app.include_router(otp.router)
app.include_router(agent_workflow.router)
app.include_router(events.router)

# Register Admin API Routers under /api
app.include_router(admin_dashboard.router, prefix=settings.API_PREFIX)
app.include_router(admin_users.router, prefix=settings.API_PREFIX)
app.include_router(admin_hospitals.router, prefix=settings.API_PREFIX)
app.include_router(admin_claims.router, prefix=settings.API_PREFIX)
app.include_router(admin_documents.router, prefix=settings.API_PREFIX)
app.include_router(admin_appointments.router, prefix=settings.API_PREFIX)
app.include_router(admin_insurances.router, prefix=settings.API_PREFIX)
app.include_router(admin_schemes.router, prefix=settings.API_PREFIX)
app.include_router(admin_notifications.router, prefix=settings.API_PREFIX)
app.include_router(admin_analytics.router, prefix=settings.API_PREFIX)
app.include_router(admin_ai_insights.router, prefix=settings.API_PREFIX)
app.include_router(admin_audit_logs.router, prefix=settings.API_PREFIX)
app.include_router(admin_knowledge_base.router, prefix=settings.API_PREFIX)
app.include_router(admin_hospital_media.router, prefix=settings.API_PREFIX)
app.include_router(admin_ai_monitoring.router, prefix=settings.API_PREFIX)
app.include_router(admin_rag_debug.router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["Health"])
@app.get("/server-health", tags=["Health"])
def server_health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": "MySQL",
        "ai_enabled": settings.AI_ENABLED,
        "environment": settings.ENVIRONMENT,
        "version": "2.3.0"
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to MedSentinel API with AI Intelligence & Admin Dashboard",
        "docs": "/docs",
        "health": "/server-health"
    }
