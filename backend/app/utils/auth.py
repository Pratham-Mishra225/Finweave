"""Authentication utilities for Firebase token verification."""
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from typing import Optional


security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Verify Firebase ID token and return decoded token.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        Decoded token containing user info
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


async def get_current_user(token: dict = Depends(verify_firebase_token)) -> dict:
    """
    Get current authenticated user from token.
    
    Args:
        token: Decoded Firebase token
        
    Returns:
        User information from token
    """
    return {
        "uid": token.get("uid"),
        "email": token.get("email"),
        "name": token.get("name"),
        "email_verified": token.get("email_verified", False)
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(lambda: None)
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional HTTP Authorization credentials
        
    Returns:
        User info dict if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "email_verified": decoded_token.get("email_verified", False)
        }
    except Exception:
        return None
