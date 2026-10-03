from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User, AIConversation, AIMessage
from app.ai.agent import AIAgentService
from app.ai.private_agent import PrivateAIAgentService
from app.ai.provider import AIProvider, AIProviderError
from app.rag.vector_store import VectorStore
from app.schemas.private_ai import PrivateChatRequest, PrivateChatResponse, AIHealthResponse

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

class AIChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    mode: Optional[str] = "internal_assistant"

class AIChatResponse(BaseModel):
    conversation_id: str
    response: str
    tools_used: List[str] = []
    sources: List[Dict[str, Any]] = []
    found_in_private_data: bool = True
    suggested_actions: List[Dict[str, Any]] = []

class AIConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    message_count: int

    model_config = ConfigDict(from_attributes=True)

class AIMessageDetail(BaseModel):
    id: int
    sender: str
    content: str
    tools_used: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)

@router.get("/health", response_model=AIHealthResponse)
def get_ai_health():
    """
    Check the health, configuration, and readiness of the Private AI & Vector DB subsystems.
    Never exposes secret keys.
    """
    health = AIProvider.get_health()
    health["indexed_vectors"] = VectorStore.get_indexed_points_count()
    return health

@router.post("/private-chat", response_model=PrivateChatResponse)
async def private_chat_with_ai(
    req: PrivateChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Strict Enterprise Private Knowledge RAG chat.
    Answers strictly from authorized MedSentinel datasets and empanelled hospital knowledge.
    """
    try:
        result = await PrivateAIAgentService.chat(
            db=db,
            user=current_user,
            message=req.message,
            conversation_id=req.conversation_id,
            mode=req.mode or "strict_private"
        )
        return result
    except AIProviderError as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "AI_INTERNAL_ERROR", "message": f"Unexpected error: {str(e)}"}
        )

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_ai(
    req: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Main Assistant endpoint. Combines private RAG knowledge with authorized patient tools.
    """
    try:
        result = await PrivateAIAgentService.chat(
            db=db,
            user=current_user,
            message=req.message,
            conversation_id=req.conversation_id,
            mode=req.mode or "internal_assistant"
        )
        return {
            "conversation_id": result["conversation_id"],
            "response": result["response"],
            "tools_used": [s.get("title") for s in result.get("sources", [])] if result.get("sources") else ["private_rag_engine"],
            "sources": result.get("sources", []),
            "found_in_private_data": result.get("found_in_private_data", True),
            "suggested_actions": result.get("suggested_actions", [])
        }
    except AIProviderError as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "AI_INTERNAL_ERROR", "message": f"Unexpected error: {str(e)}"}
        )

@router.get("/conversations", response_model=List[AIConversationSummary])
def list_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all AI chat conversations belonging to the authenticated user."""
    convs = db.query(AIConversation).filter(
        AIConversation.user_id == current_user.id
    ).order_by(AIConversation.updated_at.desc()).all()

    results = []
    for c in convs:
        count = db.query(AIMessage).filter(AIMessage.conversation_id == c.id).count()
        results.append(AIConversationSummary(
            id=c.id,
            title=c.title,
            created_at=c.created_at.isoformat() if c.created_at else "",
            message_count=count
        ))

    return results

@router.get("/conversations/{conversation_id}", response_model=List[AIMessageDetail])
def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full message history for a specific conversation belonging to the user."""
    conv = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )

    messages = db.query(AIMessage).filter(
        AIMessage.conversation_id == conversation_id
    ).order_by(AIMessage.created_at.asc()).all()

    return [
        AIMessageDetail(
            id=m.id,
            sender=m.sender,
            content=m.content,
            tools_used=m.tools_used,
            created_at=m.created_at.isoformat() if m.created_at else ""
        )
        for m in messages
    ]

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an AI conversation and its message records."""
    conv = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )

    db.delete(conv)
    db.commit()
    return None
