from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, String as SQLAlchemyString
from cryptography.fernet import Fernet
from xsc_lib.xsc_lib_common.config import settings

SQLALCHEMY_DATABASE_URL = "sqlite:///./ring_tokens.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class EncryptedString(TypeDecorator):
    """
    Encrypts a string value before persisting to the database,
    and decrypts it upon retrieval.
    """
    impl = SQLAlchemyString
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        f = Fernet(settings.RING_ENCRYPTION_KEY.encode('utf-8'))
        return f.encrypt(value.encode('utf-8')).decode('utf-8')

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        f = Fernet(settings.RING_ENCRYPTION_KEY.encode('utf-8'))
        return f.decrypt(value.encode('utf-8')).decode('utf-8')


class RingToken(Base):
    __tablename__ = "ring_tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(EncryptedString, nullable=False)
    refresh_token = Column(EncryptedString, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    account_id = Column(String, nullable=False, unique=True)
    is_claimed = Column(Integer, default=0) # 0 for False, 1 for True
    user_identifier = Column(String, nullable=True) # The partner user email
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class RingWebhookEvent(Base):
    __tablename__ = "ring_webhook_events"

    request_id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())

class RingDeviceCache(Base):
    __tablename__ = "ring_device_cache"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    metadata_json = Column(JSON, nullable=False)
    capabilities_json = Column(JSON, nullable=False)
    status = Column(String, nullable=True)
    last_synced_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
