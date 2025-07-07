from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verify admin bearer token"""
    if credentials.credentials != settings.ADMIN_BEARER_TOKEN:
        logger.warning(
            f"Invalid admin token attempt: {credentials.credentials[:10]}..."
        )
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return credentials.credentials
