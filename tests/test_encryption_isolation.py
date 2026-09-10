import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from xsc_lib.xsc_lib_common import database
from xsc_lib.xsc_lib_common.config import settings

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    database.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_encryption_at_rest(test_db):
    """
    Verify that the access_token and refresh_token are encrypted when stored in SQLite.
    """
    from datetime import datetime, timedelta
    
    plaintext_access = "super-secret-access-token"
    plaintext_refresh = "super-secret-refresh-token"
    
    token = database.RingToken(
        account_id="acc_123",
        access_token=plaintext_access,
        refresh_token=plaintext_refresh,
        expires_at=datetime.utcnow() + timedelta(hours=1),
        is_claimed=1
    )
    test_db.add(token)
    test_db.commit()
    
    from sqlalchemy import text
    # Query raw database to bypass SQLAlchemy TypeDecorator
    raw_result = test_db.execute(text("SELECT access_token, refresh_token FROM ring_tokens WHERE account_id='acc_123'")).fetchone()
    raw_access = raw_result[0]
    raw_refresh = raw_result[1]
    
    assert raw_access != plaintext_access
    assert raw_refresh != plaintext_refresh
    assert raw_access.startswith("gAAAAA") # Fernet prefix
    
    # Query via SQLAlchemy to ensure decryption works
    retrieved = test_db.query(database.RingToken).filter_by(account_id="acc_123").first()
    assert retrieved.access_token == plaintext_access
    assert retrieved.refresh_token == plaintext_refresh

def test_account_isolation(test_db):
    """
    Verify that tokens are explicitly isolated by account_id.
    """
    from datetime import datetime, timedelta
    from xsc_lib.xsc_lib_extn.ring.client import RingClient
    
    token1 = database.RingToken(
        account_id="userA",
        access_token="tokA",
        refresh_token="refA",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        is_claimed=1
    )
    token2 = database.RingToken(
        account_id="userB",
        access_token="tokB",
        refresh_token="refB",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        is_claimed=1
    )
    test_db.add_all([token1, token2])
    test_db.commit()
    
    # Client initialized for userA should only see userA's token
    client_a = RingClient(test_db, account_id="userA")
    import asyncio
    token_val = asyncio.run(client_a._get_access_token())
    assert token_val == "tokA"
    
    client_b = RingClient(test_db, account_id="userB")
    token_val = asyncio.run(client_b._get_access_token())
    assert token_val == "tokB"
