import os
import sys
from sqlalchemy import create_engine, text
from cryptography.fernet import Fernet
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

key = os.getenv("RING_ENCRYPTION_KEY")
if not key:
    logger.error("No RING_ENCRYPTION_KEY found in .env")
    sys.exit(1)

f = Fernet(key.encode('utf-8'))
engine = create_engine("sqlite:///./ring_tokens.db")

def is_encrypted(token: str) -> bool:
    try:
        f.decrypt(token.encode('utf-8'))
        return True
    except Exception:
        return False

def migrate():
    with engine.begin() as conn:
        result = conn.execute(text("SELECT id, access_token, refresh_token FROM ring_tokens"))
        rows = result.fetchall()
        
        for row in rows:
            token_id = row[0]
            access_token = row[1]
            refresh_token = row[2]
            
            updates = {}
            if not is_encrypted(access_token):
                updates["access_token"] = f.encrypt(access_token.encode('utf-8')).decode('utf-8')
                
            if not is_encrypted(refresh_token):
                updates["refresh_token"] = f.encrypt(refresh_token.encode('utf-8')).decode('utf-8')
                
            if updates:
                logger.info(f"Encrypting tokens for record ID {token_id}")
                if "access_token" in updates and "refresh_token" in updates:
                    conn.execute(
                        text("UPDATE ring_tokens SET access_token = :at, refresh_token = :rt WHERE id = :id"),
                        {"at": updates["access_token"], "rt": updates["refresh_token"], "id": token_id}
                    )
                elif "access_token" in updates:
                    conn.execute(
                        text("UPDATE ring_tokens SET access_token = :at WHERE id = :id"),
                        {"at": updates["access_token"], "id": token_id}
                    )
                elif "refresh_token" in updates:
                    conn.execute(
                        text("UPDATE ring_tokens SET refresh_token = :rt WHERE id = :id"),
                        {"rt": updates["refresh_token"], "id": token_id}
                    )
                    
        from xsc_lib.xsc_lib_common import database
    
    database.Base.metadata.create_all(bind=engine)
    logger.info("Migration and table creation complete.")

if __name__ == "__main__":
    migrate()
