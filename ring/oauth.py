import httpx
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import database
from config import settings
import urllib.parse
import hmac
import hashlib
import base64
import time

logger = logging.getLogger(__name__)

RING_TOKEN_URL = "https://oauth.ring.com/oauth/token"
AVA_BASE_URL = "https://api.amazonvision.com"

async def exchange_token(code: str, db: Session):
    """
    Exchanges the authorization code from Ring for tokens, retrieves the Account ID,
    and stores it as an unclaimed token.
    """
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.RING_CLIENT_ID,
        "client_secret": settings.RING_CLIENT_SECRET,
        "code": code
    }
    
    logger.info("Initiating one-way token exchange with Ring...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(RING_TOKEN_URL, data=data)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed with status {response.status_code}")
            raise Exception("Token exchange failed")
            
        token_data = response.json()
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data.get("expires_in", 14400)
        
        # Retrieve Account ID
        user_response = await client.get(
            f"{AVA_BASE_URL}/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_response.status_code != 200:
            logger.error("Failed to fetch Account ID from Amazon Vision API")
            raise Exception("Failed to fetch Account ID")
            
        account_id = user_response.json().get("data", {}).get("id")
        if not account_id:
            raise Exception("Account ID missing in response")
            
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Upsert unclaimed token for this account_id
        existing = db.query(database.RingToken).filter_by(account_id=account_id).first()
        if existing:
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.expires_at = expires_at
            existing.is_claimed = 0
            existing.user_identifier = None
        else:
            new_token = database.RingToken(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                account_id=account_id,
                is_claimed=0
            )
            db.add(new_token)
            
        db.commit()
        logger.info("Token exchange successful. Unclaimed token stored.")
        return True

async def complete_linking(nonce: str, time_param: str, user_email: str, db: Session):
    """
    Validates the nonce against unclaimed tokens and completes the App Integrations API flow.
    """
    current_time_ms = int(time.time() * 1000)
    time_delta_seconds = (current_time_ms - int(time_param)) / 1000
    
    if time_delta_seconds > 600 or time_delta_seconds < 0:
        raise Exception("Link request expired or invalid")
        
    hmac_secret = settings.RING_HMAC_SECRET.encode('utf-8')
    matched_token = None
    
    unclaimed_tokens = db.query(database.RingToken).filter_by(is_claimed=0).all()
    for token_record in unclaimed_tokens:
        payload = f"{time_param}:{token_record.account_id}".encode('utf-8')
        mac = hmac.new(hmac_secret, payload, hashlib.sha256).digest()
        computed_nonce = base64.urlsafe_b64encode(mac).rstrip(b'=').decode('utf-8')
        
        # Constant-time comparison
        if hmac.compare_digest(computed_nonce, nonce):
            matched_token = token_record
            break
            
    if not matched_token:
        raise Exception("Invalid nonce or no matching unclaimed token found")
        
    # Claim the token
    matched_token.is_claimed = 1
    matched_token.user_identifier = user_email
    db.commit()
    
    # Notify Ring via App-Integrations API
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {matched_token.access_token}"}
        
        # 1. POST to verify
        post_data = {
            "account_identifier": user_email,
            "nonce": nonce
        }
        post_resp = await client.post(f"{AVA_BASE_URL}/v1/accounts/me/app-integrations", json=post_data, headers=headers)
        if post_resp.status_code not in (200, 201, 204):
            logger.error(f"POST app-integrations failed: {post_resp.status_code}")
            raise Exception("Failed to verify integration with Ring")
            
        # 2. PATCH to complete
        patch_data = {"status": "completed"}
        patch_resp = await client.patch(f"{AVA_BASE_URL}/v1/accounts/me/app-integrations", json=patch_data, headers=headers)
        if patch_resp.status_code not in (200, 201, 204):
            logger.error(f"PATCH app-integrations failed: {patch_resp.status_code}")
            raise Exception("Failed to finalize integration with Ring")
            
    logger.info(f"Account linking successfully completed for {user_email}")
    return True
