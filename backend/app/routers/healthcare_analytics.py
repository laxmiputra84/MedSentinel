"""
MedSentinel Agentic Architecture — AI Healthcare Data Analyst Router
Exposes DuckDB in-memory OLAP analytics, AST-validated SQL query runner,
and automatic tabular profiling for healthcare administrators and researchers.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import os
import shutil

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_any_admin
from app.models.user import User
from app.agents.data_analyst_agent import DataAnalystAgent, SQLValidationError

router = APIRouter(prefix="/analytics", tags=["Healthcare Data Analytics (DuckDB)"])

analyst_agent = DataAnalystAgent()


class AnalyticsQueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute against the active healthcare dataset")
    limit: Optional[int] = Field(default=100, ge=1, le=500)


class AnalyticsQueryResponse(BaseModel):
    success: bool
    query: str
    columns: List[str]
    row_count: int
    data: List[Dict[str, Any]]
    recommended_chart: str


@router.post("/query", response_model=AnalyticsQueryResponse)
def execute_analytics_query(
    req: AnalyticsQueryRequest,
    current_user: User = Depends(require_any_admin),
):
    """
    Executes a read-only DuckDB SQL query against the healthcare analytics dataset.
    Protected by AST validation: blocks all DDL and DML commands.
    """
    try:
        import duckdb
        conn = duckdb.connect(database=":memory:")

        # Load default embedded healthcare dataset
        conn.execute("""
            CREATE TABLE healthcare_records AS SELECT * FROM (
                VALUES 
                (101, 'Cardiology', 45000.0, 'Approved', 45, 'Male', '2026-08-10'),
                (102, 'Oncology', 125000.0, 'Approved', 62, 'Female', '2026-08-14'),
                (103, 'Orthopedics', 38000.0, 'Rejected', 38, 'Male', '2026-08-18'),
                (104, 'Cardiology', 62000.0, 'Approved', 58, 'Female', '2026-08-22'),
                (105, 'Pediatrics', 15000.0, 'Approved', 8, 'Male', '2026-08-25'),
                (106, 'Neurology', 95000.0, 'Approved', 51, 'Female', '2026-08-28'),
                (107, 'Oncology', 140000.0, 'Approved', 67, 'Male', '2026-09-02'),
                (108, 'General Surgery', 42000.0, 'Approved', 43, 'Female', '2026-09-05'),
                (109, 'Cardiology', 78000.0, 'Rejected', 72, 'Male', '2026-09-08'),
                (110, 'Orthopedics', 55000.0, 'Approved', 34, 'Female', '2026-09-12')
            ) AS t(claim_id, department, amount, status, patient_age, patient_gender, record_date);
            CREATE VIEW dataset AS SELECT * FROM healthcare_records;
        """)

        res = analyst_agent.execute_analytical_query(conn, req.query, limit=req.limit)
        conn.close()

        return AnalyticsQueryResponse(
            success=True,
            query=res["query"],
            columns=res["columns"],
            row_count=res["row_count"],
            data=res["data"],
            recommended_chart=res["recommended_chart"]
        )

    except SQLValidationError as sve:
        raise HTTPException(status_code=400, detail=str(sve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DuckDB execution error: {str(e)}")


@router.get("/profile")
def get_dataset_profile(
    current_user: User = Depends(require_any_admin),
):
    """Calculates automated exploratory data analysis (EDA) statistics."""
    try:
        import duckdb
        conn = duckdb.connect(database=":memory:")
        conn.execute("""
            CREATE TABLE dataset AS SELECT * FROM (
                VALUES 
                (101, 'Cardiology', 45000.0, 'Approved', 45, 'Male'),
                (102, 'Oncology', 125000.0, 'Approved', 62, 'Female'),
                (103, 'Orthopedics', 38000.0, 'Rejected', 38, 'Male'),
                (104, 'Cardiology', 62000.0, 'Approved', 58, 'Female'),
                (105, 'Pediatrics', 15000.0, 'Approved', 8, 'Male'),
                (106, 'Neurology', 95000.0, 'Approved', 51, 'Female')
            ) AS t(claim_id, department, amount, status, patient_age, patient_gender);
        """)
        profile = analyst_agent.analyze_dataset_profile(conn, "dataset")
        conn.close()
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profiling failed: {str(e)}")
