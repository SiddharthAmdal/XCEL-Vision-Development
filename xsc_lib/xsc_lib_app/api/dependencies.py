from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from xsc_lib.xsc_lib_common import database

security = HTTPBearer()

def get_dev_account_id(db: Session = Depends(database.get_db), token: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    DEVELOPMENT-ONLY AUTHENTICATION CONTEXT
    For MVP, any token is accepted and it resolves to the first claimed Ring account in the database.
    Production will replace this with real JWT/OIDC claims.
    """
    # Simply mapping to the known Ring account ID for the MVP
    ring_token = db.query(database.RingToken).filter_by(is_claimed=1).first()
    if not ring_token:
        raise HTTPException(status_code=500, detail="No linked Ring account found in the system for MVP.")
    return ring_token.account_id
