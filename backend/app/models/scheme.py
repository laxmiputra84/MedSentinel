from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base

class Scheme(Base):
    __tablename__ = "schemes"
    __table_args__ = {"mysql_engine": "InnoDB"}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    coverage = Column(String(100), nullable=True)
    eligibility = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    max_income = Column(String(100), nullable=True)
    type = Column(String(50), nullable=True)
