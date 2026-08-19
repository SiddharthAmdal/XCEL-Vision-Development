import httpx
from sqlalchemy.orm import Session
import database
import logging
from datetime import datetime, timedelta
import asyncio
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed
import time

logger = logging.getLogger(__name__)

_refresh_locks: dict[str, asyncio.Lock] = {}

class RateLimitException(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after} seconds.")

def custom_wait_for_rate_limit(retry_state):
    """Wait strategy that respects the Retry-After header."""
    if retry_state.outcome.failed:
        exc = retry_state.outcome.exception()
        if isinstance(exc, RateLimitException):
            return exc.retry_after
    return 1 # Default wait if no header was provided

class RingClient:
    """
    Thin HTTP client wrapper to make authenticated calls to Ring.
    """
    def __init__(self, db: Session, account_id: str):
        if not account_id:
            raise ValueError("account_id is required to initialize RingClient")
        self.db = db
        self.account_id = account_id
        self.base_url = "https://api.amazonvision.com"
        
    async def _get_access_token(self) -> str:
        token_record = self.db.query(database.RingToken).filter_by(account_id=self.account_id, is_claimed=1).first()
        if not token_record:
            raise Exception(f"No claimed Ring token found for account_id {self.account_id}. Please link account first.")
        
        # Check expiration and refresh if necessary
        if token_record.expires_at < datetime.utcnow() + timedelta(minutes=5):
            return await self._refresh_token()
            
        return token_record.access_token

    async def _refresh_token(self) -> str:
        import httpx
        from config import settings
        
        if self.account_id not in _refresh_locks:
            _refresh_locks[self.account_id] = asyncio.Lock()
            
        async with _refresh_locks[self.account_id]:
            # Re-read token state after acquiring lock to prevent double refresh
            token_record = self.db.query(database.RingToken).filter_by(account_id=self.account_id, is_claimed=1).first()
            if not token_record:
                raise Exception("Token record vanished during refresh")
                
            if token_record.expires_at >= datetime.utcnow() + timedelta(minutes=5):
                logger.info("Token was already refreshed by another concurrent request. Reusing new token.")
                return token_record.access_token
                
            logger.info(f"Refreshing Ring access token for account {self.account_id}...")
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": token_record.refresh_token,
                "client_id": settings.RING_CLIENT_ID,
                "client_secret": settings.RING_CLIENT_SECRET
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post("https://oauth.ring.com/oauth/token", data=data)
                if response.status_code != 200:
                    logger.error(f"Failed to refresh token: {response.status_code}")
                    raise Exception("Token refresh failed")
                    
                token_data = response.json()
                token_record.access_token = token_data["access_token"]
                token_record.refresh_token = token_data.get("refresh_token", token_record.refresh_token)
                expires_in = token_data.get("expires_in", 14400)
                token_record.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                self.db.commit()
                logger.info(f"Token refreshed successfully for account {self.account_id}")
                return token_record.access_token

    @retry(stop=stop_after_attempt(3), wait=custom_wait_for_rate_limit, retry=retry_if_exception_type(RateLimitException))
    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self._make_request("GET", endpoint, **kwargs)

    @retry(stop=stop_after_attempt(3), wait=custom_wait_for_rate_limit, retry=retry_if_exception_type(RateLimitException))
    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self._make_request("POST", endpoint, **kwargs)
            
    @retry(stop=stop_after_attempt(3), wait=custom_wait_for_rate_limit, retry=retry_if_exception_type(RateLimitException))
    async def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self._make_request("DELETE", endpoint, **kwargs)

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        token = await self._get_access_token()
        headers = kwargs.pop("headers", {})
        if "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {token}"
        if "Accept" not in headers:
            headers["Accept"] = "application/json"
            
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            if response.status_code == 429:
                retry_after_header = response.headers.get("Retry-After")
                retry_after = int(retry_after_header) if retry_after_header and retry_after_header.isdigit() else 2
                logger.warning(f"Rate limited on {method} {endpoint}, retrying after {retry_after}s")
                raise RateLimitException(retry_after=retry_after)
            return response
