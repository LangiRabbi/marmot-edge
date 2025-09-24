"""
JWT Authentication system for WebSocket and API endpoints.
Provides secure token generation, validation, and user management.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration from environment
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token payload data structure."""

    user_id: Optional[str] = None
    username: Optional[str] = None
    permissions: list[str] = []
    workstation_access: list[str] = []  # List of workstation IDs user can access


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in token
        expires_delta: Custom expiration time (defaults to ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if token is expired
        exp = payload.get("exp")
        if exp is None:
            return None

        if datetime.utcnow() > datetime.fromtimestamp(exp):
            return None

        return payload

    except JWTError:
        return None


def get_current_user(token: str) -> Optional[TokenData]:
    """
    Extract user information from JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData object or None if invalid
    """
    payload = verify_token(token)
    if payload is None:
        return None

    try:
        user_id = payload.get("sub")
        username = payload.get("username")
        permissions = payload.get("permissions", [])
        workstation_access = payload.get("workstation_access", [])

        if user_id is None:
            return None

        return TokenData(
            user_id=user_id,
            username=username,
            permissions=permissions,
            workstation_access=workstation_access,
        )
    except Exception:
        return None


def create_demo_token(
    user_id: str = "demo_user",
    username: str = "demo",
    workstation_ids: list[str] = None,
) -> str:
    """
    Create a demo token for development/testing.

    Args:
        user_id: User identifier
        username: Username
        workstation_ids: List of workstation IDs user can access (defaults to all)

    Returns:
        JWT token string
    """
    if workstation_ids is None:
        workstation_ids = ["*"]  # Access to all workstations

    token_data = {
        "sub": user_id,
        "username": username,
        "permissions": ["read", "write", "admin"],
        "workstation_access": workstation_ids,
    }

    return create_access_token(data=token_data)


def check_workstation_access(user: TokenData, workstation_id: str) -> bool:
    """
    Check if user has access to specific workstation.

    Args:
        user: User token data
        workstation_id: Workstation ID to check access for

    Returns:
        True if user has access, False otherwise
    """
    if not user or not user.workstation_access:
        return False

    # Check for wildcard access
    if "*" in user.workstation_access:
        return True

    # Check for specific workstation access
    return workstation_id in user.workstation_access


def check_permission(user: TokenData, required_permission: str) -> bool:
    """
    Check if user has specific permission.

    Args:
        user: User token data
        required_permission: Permission to check (e.g., "read", "write", "admin")

    Returns:
        True if user has permission, False otherwise
    """
    if not user or not user.permissions:
        return False

    # Admin permission grants all access
    if "admin" in user.permissions:
        return True

    return required_permission in user.permissions
