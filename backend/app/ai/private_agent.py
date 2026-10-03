import uuid
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import User, AIConversation, AIMessage
from app.models.ai_monitoring import AIRequestLog
from app.agents.planner_agent import PlannerAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.hospital_agent import HospitalAgent
from app.agents.claims_agent import ClaimsAgent
from app.agents.appointment_agent import AppointmentAgent
from app.agents.eligibility_agent import EligibilityAgent
from app.agents.document_agent import DocumentAgent
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.response_agent import ResponseAgent
from app.ai.provider import AIProviderError

class PrivateAIAgentService:
    @staticmethod
    async def chat(
        db: Session,
        user: User,
        message: str,
        conversation_id: Optional[str] = None,
        mode: str = "strict_private"
    ) -> Dict[str, Any]:
        """
        Executes private enterprise chat pipeline with RBAC enforcement and RAG knowledge retrieval.
        """
        start_time = time.time()

        # 1. Safety & Rate Limiting Check
        is_safe, safety_error = SafetyAgent.validate_input(user.id, message)
        if not is_safe:
            # Log security event
            PrivateAIAgentService._log_request(
                db=db,
                user_id=user.id,
                conversation_id=conversation_id,
                status="RATE_LIMITED" if "rate limit" in safety_error.lower() else "FILTERED",
                error_code="AI_PROVIDER_RATE_LIMITED" if "rate limit" in safety_error.lower() else "PROMPT_INJECTION_DETECTED",
                latency_ms=round((time.time() - start_time) * 1000, 2),
                query=message
            )
            return {
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "response": safety_error,
                "sources": [],
                "found_in_private_data": False,
                "mode": mode,
                "suggested_actions": []
            }

        # 2. Conversation Session Management
        if conversation_id:
            conv = db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user.id
            ).first()
            if not conv:
                conv = AIConversation(
                    id=conversation_id,
                    user_id=user.id,
                    title=message[:50] + "..." if len(message) > 50 else message
                )
                db.add(conv)
                db.commit()
        else:
            conv = AIConversation(
                id=str(uuid.uuid4()),
                user_id=user.id,
                title=message[:50] + "..." if len(message) > 50 else message
            )
            db.add(conv)
            db.commit()
            conversation_id = conv.id

        # 3. Planner Agent - Intent & Mode Planning
        plan = PlannerAgent.plan(
            user_message=message,
            user_role=user.role or "USER",
            requested_mode=mode
        )

        # 4. Execute Retrieval Agent (Private Datasets with RBAC)
        rag_result = await RetrievalAgent.retrieve(
            query=message,
            user_role=user.role or "USER",
            user_id=user.id,
            mode=mode,
            db=db
        )

        # 5. Execute Authorized Specialized Tool Agents (if applicable)
        tool_data = {}
        target_agent = plan.get("target_agent")

        if target_agent == "hospital_agent":
            tool_data = await HospitalAgent.get_hospital_data(query=message, db=db)
        elif target_agent == "claims_agent":
            tool_data = await ClaimsAgent.get_user_claims_data(user_id=user.id, user_role=user.role or "USER", db=db)
        elif target_agent == "appointment_agent":
            tool_data = await AppointmentAgent.get_user_appointments_data(user_id=user.id, user_role=user.role or "USER", db=db)
        elif target_agent == "eligibility_agent":
            tool_data = await EligibilityAgent.evaluate_schemes(db=db)
        elif target_agent == "document_agent":
            tool_data = await DocumentAgent.get_user_documents_data(user_id=user.id, user_role=user.role or "USER", db=db)
        elif target_agent == "analytics_agent":
            tool_data = await AnalyticsAgent.get_aggregated_analytics(user_role=user.role or "USER", db=db)

        # 6. Response Agent - Generate response with zero hallucination enforcement
        try:
            final_res = await ResponseAgent.generate_final_response(
                user_message=message,
                rag_result=rag_result,
                tool_data=tool_data if tool_data else None,
                mode=mode,
                user_role=user.role or "USER"
            )
        except AIProviderError as e:
            PrivateAIAgentService._log_request(
                db=db,
                user_id=user.id,
                conversation_id=conversation_id,
                status="ERROR",
                error_code=e.code,
                latency_ms=round((time.time() - start_time) * 1000, 2),
                query=message
            )
            raise e

        latency = round((time.time() - start_time) * 1000, 2)

        # 7. Persist Message History
        user_msg_record = AIMessage(
            conversation_id=conversation_id,
            sender="user",
            content=message
        )
        asst_msg_record = AIMessage(
            conversation_id=conversation_id,
            sender="assistant",
            content=final_res["response"],
            tools_used=json.dumps([target_agent] if target_agent else [])
        )
        db.add(user_msg_record)
        db.add(asst_msg_record)
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()

        # 8. Log AI Request Telemetry
        PrivateAIAgentService._log_request(
            db=db,
            user_id=user.id,
            conversation_id=conversation_id,
            status="SUCCESS",
            latency_ms=latency,
            tokens_used=final_res.get("tokens_used", 0),
            provider=final_res.get("provider", "gemini"),
            model=final_res.get("model", "gemini-1.5-flash"),
            datasets_used=[s.get("title") for s in final_res.get("sources", [])],
            tools_used=[target_agent] if target_agent else [],
            query=message
        )

        return {
            "conversation_id": conversation_id,
            "response": final_res["response"],
            "sources": final_res.get("sources", []),
            "found_in_private_data": final_res.get("found_in_private_data", False),
            "mode": mode,
            "suggested_actions": final_res.get("suggested_actions", [])
        }

    @staticmethod
    def _log_request(
        db: Session,
        user_id: int,
        conversation_id: Optional[str],
        status: str,
        latency_ms: float,
        tokens_used: int = 0,
        provider: str = "gemini",
        model: str = "gemini-1.5-flash",
        datasets_used: Optional[List[str]] = None,
        tools_used: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        query: str = ""
    ):
        try:
            log = AIRequestLog(
                user_id=user_id,
                conversation_id=conversation_id,
                request_type="PRIVATE_CHAT",
                provider=provider,
                model=model,
                status=status,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                datasets_used=json.dumps(datasets_used or []),
                tools_used=json.dumps(tools_used or []),
                error_code=error_code,
                user_query_preview=query[:150]
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
