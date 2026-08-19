from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, HTMLResponse
import logging
import time

import database
from . import oauth, webhook, provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ring", tags=["ring"])

from fastapi import Query

@router.get("/link")
async def account_link(nonce: str = None, time_param: str = Query(None, alias="time")):
    """
    Account Link URL: Ring redirects user here with ?nonce=N&time=T.
    Validates timestamp and shows a mock login screen for the partner.
    """
    if not nonce or not time_param:
        raise HTTPException(status_code=400, detail="Missing nonce or time")
        
    current_time_ms = int(time.time() * 1000)
    time_delta_seconds = (current_time_ms - int(time_param)) / 1000
    if time_delta_seconds > 600 or time_delta_seconds < 0:
        raise HTTPException(status_code=400, detail="Link request expired")
        
    # Serve a mock login page that posts to /complete
    html_content = f"""
    <html>
        <body>
            <h2>XCEL Vision - Link Ring Account</h2>
            <form action="/api/v1/ring/link/complete" method="post">
                <input type="hidden" name="nonce" value="{nonce}">
                <input type="hidden" name="time_param" value="{time_param}">
                <label>Email: <input type="email" name="email" value="user@xcelcorp.com"></label><br><br>
                <button type="submit">Authorize and Link</button>
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/link/complete")
async def link_complete(nonce: str = Form(...), time_param: str = Form(...), email: str = Form(...), db: Session = Depends(database.get_db)):
    """
    Completes the account linking process after user 'logs in'.
    """
    try:
        await oauth.complete_linking(nonce, time_param, email, db)
        return {"status": "success", "message": "Account successfully linked with Ring."}
    except Exception as e:
        logger.error(f"Linking error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/home")
async def app_homepage(account_id: str = Query(...), db: Session = Depends(database.get_db)):
    """
    App Homepage URL: Ring requires this endpoint for the app configuration.
    Requires explicit account_id for identity isolation.
    """
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id is required")
        
    token_exists = db.query(database.RingToken).filter_by(account_id=account_id, is_claimed=1).first() is not None
    return {
        "service": "XCEL Vision",
        "ring_integration": "configured" if token_exists else "pending",
        "status": "development"
    }

@router.post("/token")
async def token_exchange(code: str = Form(...), db: Session = Depends(database.get_db)):
    """
    Token Exchange URL: Called by Ring with the authorization code.
    """
    try:
        await oauth.exchange_token(code, db)
        return {"status": "success", "message": "Token exchanged"}
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise HTTPException(status_code=400, detail="Token exchange failed")

@router.post("/webhook")
async def webhook_handler(request: Request, db: Session = Depends(database.get_db)):
    """
    Webhook URL: Receives events from Ring.
    """
    try:
        normalized_event = await webhook.process_webhook(request, db)
        if normalized_event is None:
            logger.info("Webhook duplicate detected: Skipping processing.")
            return JSONResponse(content={"status": "acknowledged", "detail": "duplicate"}, status_code=200)
            
        logger.info(f"Received valid Ring event: {normalized_event.event_type} for camera {normalized_event.camera_id}")
        return JSONResponse(content={"status": "acknowledged"}, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error("Unhandled error processing webhook")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/test/capabilities")
async def test_capabilities(account_id: str = Query(...), db: Session = Depends(database.get_db)):
    """
    Internal dev endpoint to produce the Ring Capability Report.
    Requires explicit account_id.
    """
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id is required")
        
    ring_provider = provider.RingCameraProvider(db, account_id)
    try:
        report = await ring_provider.generate_capability_report()
        return report
    except Exception as e:
        logger.error(f"Failed to generate capability report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
