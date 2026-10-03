from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Configure SQLAlchemy engine for MySQL with production-ready connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

def get_db():
    """Dependency for yielding database sessions per request and guaranteeing cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def sync_database_schema(target_engine=engine, declarative_base=Base):
    """
    Ensures that all tables and missing columns defined in SQLAlchemy models
    are created and synced to the underlying MySQL database safely.
    """
    from sqlalchemy import inspect, text
    declarative_base.metadata.create_all(bind=target_engine)
    inspector = inspect(target_engine)
    existing_tables = set(inspector.get_table_names())

    for table_name, table in declarative_base.metadata.tables.items():
        if table_name in existing_tables:
            existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(target_engine.dialect)
                    nullable = "NULL" if col.nullable else "NOT NULL"
                    alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col.name}` {col_type} {nullable}"
                    with target_engine.begin() as conn:
                        conn.execute(text(alter_sql))
                    print(f"Auto-migration: Added missing column '{col.name}' ({col_type}) to table '{table_name}'.")

