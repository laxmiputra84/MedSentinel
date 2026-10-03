from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class LabTestItem(BaseModel):
    name: str
    value: float
    unit: str
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    status: Optional[str] = "NORMAL"
    is_critical: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)

class LabExtractionResponse(BaseModel):
    patient_name: str
    patient_id: str
    report_date: str
    report_type: str = "Lab Report"
    tests: List[LabTestItem]

    model_config = ConfigDict(from_attributes=True)

class LabTestTrendPoint(BaseModel):
    date: str
    value: float

    model_config = ConfigDict(from_attributes=True)
