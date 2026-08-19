import hmac
import hashlib
from fastapi import Request, HTTPException
import logging
from config import settings
from .models import XcelEvent
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import RingWebhookEvent

logger = logging.getLogger(__name__)

def verify_ring_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Verifies the HMAC-SHA256 signature from Ring.
    The signature is expected to be a hex string.
    """
    if not signature_header:
        return False
        
    hmac_secret = settings.RING_HMAC_SECRET.encode('utf-8')
    
    # Calculate the HMAC-SHA256 of the raw body
    calculated_hmac = hmac.new(
        hmac_secret,
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    # Use hmac.compare_digest for constant-time comparison to prevent timing attacks
    return hmac.compare_digest(calculated_hmac, signature_header)

async def process_webhook(request: Request, db: Session) -> XcelEvent:
    """
    Reads the raw request, verifies the signature, performs atomic idempotency check, and normalizes the event.
    """
    raw_body = await request.body()
    
    signature_header = request.headers.get("x-signature")
    logger.info(f"Received headers: {request.headers}")
    
    if not signature_header:
        logger.warning("Webhook rejected: Missing signature header")
        raise HTTPException(status_code=401, detail="Missing signature")
        
    # Handle the 'sha256=' prefix if present
    signature = signature_header
    if signature.startswith("sha256="):
        signature = signature[7:]
        
    if not verify_ring_webhook_signature(raw_body, signature):
        logger.warning("Webhook rejected: Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
        
    # If signature is valid, process the JSON body
    try:
        payload = await request.json()
    except Exception as e:
        logger.error("Failed to parse webhook JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    # Extract Stable Event Identifier for Idempotency
    meta = payload.get("meta", {})
    request_id = meta.get("request_id")
    
    if not request_id:
        logger.error("Webhook payload missing meta.request_id")
        raise HTTPException(status_code=400, detail="Missing request_id in payload")
        
    # Atomic Idempotency Check
    try:
        new_event = RingWebhookEvent(request_id=request_id)
        db.add(new_event)
        db.commit()
    except IntegrityError:
        # The request_id already exists in the database -> Duplicate delivery
        db.rollback()
        logger.info(f"Duplicate webhook received. request_id={request_id}")
        return None # Indicate duplicate delivery to the router

    # Map Ring event to XCEL normalized event
    ring_data = payload.get("data", {})
    ring_attributes = ring_data.get("attributes", {})
    
    ring_event_type = ring_data.get("type", "unknown")
    
    # Check if the device ID is in the data relationships or attributes
    camera_id = ring_attributes.get("source", "unknown_device")
    
    # Basic mapping
    xcel_event_type = "MOTION" if ring_event_type == "button_press" else ring_event_type.upper()
    
    event_timestamp_ms = ring_attributes.get("timestamp")
    timestamp = datetime.fromtimestamp(event_timestamp_ms / 1000.0) if event_timestamp_ms else datetime.utcnow()
    
    normalized_event = XcelEvent(
        event_id=ring_data.get("id", str(uuid.uuid4())),
        camera_id=camera_id,
        event_type=xcel_event_type,
        timestamp=timestamp,
        metadata=payload
    )
    
    return normalized_event
