from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class KnowledgeDataset(Base):
    __tablename__ = "knowledge_datasets"
    __table_args__ = (
        Index("ix_knowledge_datasets_status_visibility", "status", "visibility"),
        Index("ix_knowledge_datasets_hospital", "hospital_id"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True) # PDF, DOCX, CSV, XLSX, TXT, IMAGE, MANUAL
    file_path = Column(String(500), nullable=True)
    source_type = Column(String(50), default="ADMIN_UPLOAD", nullable=False) # ADMIN_UPLOAD, EMPLOYEE_UPLOAD, HOSPITAL_RECORD, INSURANCE_DOC, SCHEME_DOC, INTERNAL_POLICY
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="UPLOADED", nullable=False, index=True) # UPLOADED, PROCESSING, READY, FAILED, DISABLED, PENDING_REVIEW, APPROVED, REJECTED
    visibility = Column(String(50), default="USER_AUTHORIZED", nullable=False, index=True) # PRIVATE_ADMIN, PRIVATE_ORGANIZATION, PRIVATE_HOSPITAL, PRIVATE_EMPLOYEE, USER_AUTHORIZED, SUPER_ADMIN_ONLY
    organization_id = Column(Integer, nullable=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    uploader = relationship("User", foreign_keys=[uploaded_by])
    hospital = relationship("Hospital", foreign_keys=[hospital_id])
    documents = relationship("KnowledgeDocument", back_populates="dataset", cascade="all, delete-orphan")
    access_rules = relationship("KnowledgeAccessRule", back_populates="dataset", cascade="all, delete-orphan")
    processing_logs = relationship("KnowledgeProcessingLog", back_populates="dataset", cascade="all, delete-orphan")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index("ix_knowledge_documents_dataset", "dataset_id"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("knowledge_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    meta_info = Column(Text, nullable=True) # JSON metadata string
    visibility = Column(String(50), default="USER_AUTHORIZED", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    dataset = relationship("KnowledgeDataset", back_populates="documents")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        Index("ix_knowledge_chunks_doc_idx", "document_id", "chunk_index"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_reference = Column(String(255), nullable=True) # Vector Point ID / Key in Qdrant
    meta_info = Column(Text, nullable=True) # JSON containing dataset_id, hospital_id, visibility, allowed_roles
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")


class KnowledgeAccessRule(Base):
    __tablename__ = "knowledge_access_rules"
    __table_args__ = (
        Index("ix_knowledge_access_rules_dataset_role", "dataset_id", "role"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("knowledge_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=True) # SUPER_ADMIN, HOSPITAL_ADMIN, INSURANCE_ADMIN, USER
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=True)
    can_read = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    dataset = relationship("KnowledgeDataset", back_populates="access_rules")
    user = relationship("User")
    hospital = relationship("Hospital")


class KnowledgeProcessingLog(Base):
    __tablename__ = "knowledge_processing_logs"
    __table_args__ = (
        Index("ix_knowledge_processing_logs_dataset", "dataset_id"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("knowledge_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False) # STARTED, EXTRACTING, CHUNKING, EMBEDDING, COMPLETED, FAILED
    message = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    dataset = relationship("KnowledgeDataset", back_populates="processing_logs")
