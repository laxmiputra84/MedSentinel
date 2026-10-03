from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.lab_result import LabTestItem

class HealthScoreResponse(BaseModel):
    health_score: int
    risk_score: int
    risk_level: str
    abnormal_tests: int
    ai_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class HealthDashboardResponse(BaseModel):
    total_documents: int
    latest_lab_reports_count: int
    normal_results_count: int
    abnormal_results_count: int
    critical_results_count: int
    health_score: int
    risk_score: int
    risk_level: str
    critical_alerts: List[LabTestItem]
    ai_summary: Optional[str] = None
    trends: Dict[str, List[Dict[str, Any]]]

    model_config = ConfigDict(from_attributes=True)
