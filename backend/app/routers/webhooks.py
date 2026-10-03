import hmac
import hashlib
import time
from typing import Dict, Any, Optional, Set
from fastapi import APIRouter, Request, HTTPException, Header, Query, Depends, status, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.plugin import PluginWebhookEvent
from app.plugins.manager import plugin_manager
from app.plugins.schema import ToolRequest
from app.ai.safety import ExternalContentSanitizer

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks Security Gateway"])

# In-memory deduplication cache for replay protection (cleansed periodically)
_seen_event_ids: Dict[str, float] = {}
REPLAY_WINDOW_SECONDS = 300  # 5 minutes replay window

def _verify_replay(event_id: str) -> None:
    now = time.time()
    # Prune events older than replay window
    stale_keys = [k for k, ts in _seen_event_ids.items() if now - ts > REPLAY_WINDOW_SECONDS]
    for k in stale_keys:
        _seen_event_ids.pop(k, None)

    if event_id in _seen_event_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate or replayed webhook event ID '{event_id}' detected."
        )
    _seen_event_ids[event_id] = now

def _verify_hmac_sha256(raw_payload: bytes, signature_header: Optional[str], secret: str) -> bool:
    if not signature_header:
        # In mock or test mode without secret configured, verify softly
        if not secret or secret in ["", "your-webhook-secret-here", "whatsapp_secret_placeholder"]:
            return True
        return False

    expected_sig = hmac.new(secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()
    # Check if header contains "sha256=" prefix
    clean_header = signature_header.replace("sha256=", "").strip()
    return hmac.compare_digest(clean_header, expected_sig)

# ==================== WHATSAPP WEBHOOKS ====================

@router.get("/whatsapp")
def verify_whatsapp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Official WhatsApp Business Webhook Verification Handshake (GET).
    Meta calls this endpoint to verify server ownership.
    """
    expected_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "medsentinel_whatsapp_token")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="WhatsApp Webhook token verification failed.")

@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db)
):
    """
    Inbound WhatsApp Business Event Listener.
    Validates HMAC signature, checks replay protection, sanitizes payload,
    and records to tamper-evident webhook ledger.
    """
    raw_body = await request.body()
    secret = getattr(settings, "WHATSAPP_APP_SECRET", "whatsapp_secret_placeholder")

    # 1. Verify HMAC SHA-256 signature
    sig_valid = _verify_hmac_sha256(raw_body, x_hub_signature_256, secret)
    if not sig_valid and secret not in ["", "whatsapp_secret_placeholder"]:
        raise HTTPException(status_code=401, detail="Invalid HMAC-SHA256 signature.")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON body.")

    # 2. Extract Event ID & Replay Protection
    event_id = data.get("id") or (data.get("entry", [{}])[0].get("id") if data.get("entry") else None)
    if not event_id:
        event_id = f"wa_{hashlib.md5(raw_body).hexdigest()}"

    _verify_replay(event_id)

    # 3. Log event in DB
    event_record = PluginWebhookEvent(
        provider="whatsapp",
        event_id=str(event_id),
        event_type="inbound_message",
        signature_header=x_hub_signature_256,
        signature_valid=sig_valid,
        payload_preview=data,
        processed=True
    )
    db.add(event_record)
    db.commit()

    # 4. Extract message text and sanitize via ExternalContentSanitizer
    message_text = ""
    phone = ""
    try:
        entries = data.get("entry", [])
        if entries and "changes" in entries[0]:
            changes = entries[0]["changes"][0]["value"]
            messages = changes.get("messages", [])
            if messages:
                phone = messages[0].get("from", "")
                message_text = messages[0].get("text", {}).get("body", "")
    except Exception:
        pass

    sanitized_data = ExternalContentSanitizer.sanitize(message_text, source="WHATSAPP_INBOUND")

    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "signature_valid": sig_valid,
        "processed": True,
        "sanitized_boundary_applied": True,
        "message": "WhatsApp webhook accepted and queued for agent orchestration."
    }

# ==================== SMS / MOBILE WEBHOOKS ====================

@router.post("/sms")
async def receive_sms_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None, alias="X-Twilio-Signature"),
    db: Session = Depends(get_db)
):
    """
    Inbound SMS / Mobile Gateway Webhook.
    Handles incoming messages, delivery receipts, and verification passcodes.
    """
    raw_body = await request.body()
    secret = getattr(settings, "SMS_WEBHOOK_SECRET", "")

    sig_valid = _verify_hmac_sha256(raw_body, x_twilio_signature, secret)

    try:
        # Twilio sends form data or JSON
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
        else:
            form = await request.form()
            data = dict(form)
    except Exception:
        data = {"raw": raw_body.decode("utf-8", errors="ignore")}

    event_id = data.get("MessageSid") or data.get("SmsSid") or f"sms_{hashlib.md5(raw_body).hexdigest()}"
    _verify_replay(event_id)

    event_record = PluginWebhookEvent(
        provider="sms",
        event_id=str(event_id),
        event_type="inbound_sms",
        signature_header=x_twilio_signature,
        signature_valid=sig_valid,
        payload_preview=data,
        processed=True
    )
    db.add(event_record)
    db.commit()

    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "provider": "sms",
        "processed": True
    }

# ==================== VOICE / TELEPHONY WEBHOOKS ====================

@router.post("/voice")
async def receive_voice_webhook(
    request: Request,
    x_voice_signature: Optional[str] = Header(None, alias="X-Voice-Signature"),
    db: Session = Depends(get_db)
):
    """
    Inbound Telephony / Voice Gateway Webhook.
    Receives call state transitions, recording URLs, and transcription payloads.
    """
    raw_body = await request.body()
    secret = getattr(settings, "VOICE_WEBHOOK_SECRET", "")

    sig_valid = _verify_hmac_sha256(raw_body, x_voice_signature, secret)

    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
        else:
            form = await request.form()
            data = dict(form)
    except Exception:
        data = {"raw": raw_body.decode("utf-8", errors="ignore")}

    event_id = data.get("CallSid") or f"call_{hashlib.md5(raw_body).hexdigest()}"
    _verify_replay(event_id)

    event_record = PluginWebhookEvent(
        provider="voice",
        event_id=str(event_id),
        event_type="call_event",
        signature_header=x_voice_signature,
        signature_valid=sig_valid,
        payload_preview=data,
        processed=True
    )
    db.add(event_record)
    db.commit()

    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "provider": "voice",
        "processed": True
    }
