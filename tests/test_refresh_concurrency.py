import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database
from ring.client import RingClient

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    database.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_refresh_concurrency(test_db):
    """
    Verify that concurrent requests triggering a refresh for the same account
    only result in a single HTTP request to the OAuth server.
    """
    token = database.RingToken(
        account_id="acc_concurrency",
        access_token="old_access",
        refresh_token="old_refresh",
        expires_at=datetime.utcnow() - timedelta(minutes=1), # expired
        is_claimed=1
    )
    test_db.add(token)
    test_db.commit()
    
    client = RingClient(test_db, account_id="acc_concurrency")
    
    # Mock httpx.AsyncClient.post to track call count and simulate delay
    call_count = 0
    
    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.5) # Simulate network delay to ensure race condition window
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "expires_in": 3600
        }
        return mock_resp

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        # Fire 3 concurrent requests that all require a valid token
        tasks = [
            client._get_access_token(),
            client._get_access_token(),
            client._get_access_token()
        ]
        results = await asyncio.gather(*tasks)
        
        # All three should return the new token
        assert all(res == "new_access" for res in results)
        
        # The mock post should have only been called once thanks to the async lock and state re-read
        assert call_count == 1
