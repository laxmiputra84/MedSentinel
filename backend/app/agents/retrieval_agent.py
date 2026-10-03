from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.rag.rag_pipeline import RAGPipeline

class RetrievalAgent:
    """
    Executes permission-enforced knowledge retrieval from private datasets.
    """
    @staticmethod
    async def retrieve(
        query: str,
        user_role: str,
        user_id: Optional[int] = None,
        user_hospital_id: Optional[int] = None,
        mode: str = "strict_private",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        return await RAGPipeline.execute_rag_query(
            query=query,
            user_role=user_role,
            user_id=user_id,
            user_hospital_id=user_hospital_id,
            mode=mode,
            db=db
        )
