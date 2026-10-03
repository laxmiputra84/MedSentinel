from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeBase(BaseModel):
    name: str
    description: Optional[str] = None
    coverage: Optional[str] = None
    eligibility: Optional[str] = None
    benefits: Optional[str] = None
    category: Optional[str] = None
    max_income: Optional[str] = None
    type: Optional[str] = None

class SchemeResponse(SchemeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
