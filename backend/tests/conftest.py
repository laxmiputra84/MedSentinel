import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models import (
    User,
    Hospital,
    Scheme,
    Insurance,
    UserInsurance,
    InsuranceClaim,
    ClaimStatusHistory,
    Appointment,
    Notification,
    UserDocument,
    AdminAuditLog,
    AIConversation,
    AIMessage,
    KnowledgeDataset,
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeAccessRule,
    KnowledgeProcessingLog,
    HospitalImage,
    AIRequestLog,
    Patient,
    LabResult,
    HealthScore,
    FraudAnalysis,
    Recommendation,
    Event,
    AgentTask,
    WorkflowInstance,
    WorkflowStepRecord,
    WorkflowEventRecord,
    WorkflowCheckpointRecord,
    HumanReviewRecord,
)

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_client():
    client = TestClient(app)
    client.cookies.clear()
    return client
