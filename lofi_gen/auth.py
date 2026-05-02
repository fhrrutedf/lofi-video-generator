"""
Authentication utilities for API.

Uses API key header for simplicity (can upgrade to JWT later).
"""

from __future__ import annotations

from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from lofi_gen.db.connection import get_db
from lofi_gen.db.models import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from API key.
    
    Supports:
      - Authorization: Bearer <api_key> header
      - X-API-Key: <api_key> header
    """
    api_key = None
    
    # Try Bearer token
    if credentials:
        api_key = credentials.credentials
    
    # Try X-API-Key header
    if not api_key and x_api_key:
        api_key = x_api_key
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Use 'Authorization: Bearer <key>' or 'X-API-Key: <key>' header"
        )
    
    user = db.query(User).filter(User.api_key == api_key).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return user


def check_quota(user: User, duration: int) -> None:
    """Check if user has quota for this request."""
    # Check tier limits
    if user.videos_generated >= user.monthly_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly limit reached. Upgrade your plan (current: {user.tier.value})"
        )
    
    # Check duration limit
    if duration > user.max_duration:
        raise HTTPException(
            status_code=400,
            detail=f"Duration exceeds limit. Max: {user.max_duration}s, Requested: {duration}s"
        )
