"""
WebSocket authentication middleware.
Handles JWT token validation for WebSocket connections.
"""

import os
from typing import Optional
from urllib.parse import parse_qs

from dotenv import load_dotenv
from fastapi import WebSocket, status
from fastapi.security import HTTPBearer

from .auth import TokenData, get_current_user
from .rate_limiting import rate_limiter

# Load environment variables first
load_dotenv()

# Security configuration
WEBSOCKET_AUTH_REQUIRED = os.getenv("WEBSOCKET_AUTH_REQUIRED", "true").lower() == "true"
security = HTTPBearer()


class WebSocketAuthError(Exception):
    """Custom exception for WebSocket authentication errors."""

    def __init__(self, code: int, reason: str):
        self.code = code
        self.reason = reason
        super().__init__(f"WebSocket auth error {code}: {reason}")


async def authenticate_websocket(websocket: WebSocket) -> Optional[TokenData]:
    """
    Authenticate WebSocket connection using JWT token.

    Args:
        websocket: WebSocket connection instance

    Returns:
        TokenData if authentication successful, None if auth disabled

    Raises:
        WebSocketAuthError: If authentication fails
    """
    # Skip auth if disabled (development mode)
    if not WEBSOCKET_AUTH_REQUIRED:
        return None

    # Extract token from query parameters
    token = _extract_token_from_query(websocket)

    if not token:
        raise WebSocketAuthError(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Missing authentication token. Use ?token=<jwt_token> in WebSocket URL",
        )

    # Validate token
    user = get_current_user(token)
    if not user:
        raise WebSocketAuthError(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired authentication token",
        )

    return user


async def authorize_workstation_access(
    user: Optional[TokenData], workstation_id: str
) -> bool:
    """
    Check if user has access to specific workstation.

    Args:
        user: User token data (None if auth disabled)
        workstation_id: Workstation ID to check access for

    Returns:
        True if access granted, False otherwise
    """
    # Allow all access if auth is disabled
    if not WEBSOCKET_AUTH_REQUIRED or user is None:
        return True

    # Import here to avoid circular import
    from .auth import check_workstation_access

    return check_workstation_access(user, workstation_id)


async def check_connection_rate_limit(
    websocket: WebSocket, user: Optional[TokenData]
) -> bool:
    """
    Check rate limits for new WebSocket connection.

    Args:
        websocket: WebSocket connection instance
        user: User token data

    Returns:
        True if connection allowed, False if rate limited

    Raises:
        WebSocketAuthError: If rate limited
    """
    # Get client IP address
    client_ip = _get_client_ip(websocket)

    # Check rate limits
    rate_check = rate_limiter.check_connection_limit(client_ip)
    if not rate_check.allowed:
        raise WebSocketAuthError(
            code=status.WS_1008_POLICY_VIOLATION, reason=rate_check.reason
        )

    return True


async def register_connection(
    websocket: WebSocket, connection_id: str, user: Optional[TokenData]
) -> bool:
    """
    Register new WebSocket connection with rate limiter.

    Args:
        websocket: WebSocket connection instance
        connection_id: Unique connection identifier
        user: User token data

    Returns:
        True if connection registered successfully
    """
    client_ip = _get_client_ip(websocket)
    user_id = user.user_id if user else None

    return rate_limiter.add_connection(connection_id, client_ip, user_id)


async def unregister_connection(connection_id: str):
    """
    Unregister WebSocket connection from rate limiter.

    Args:
        connection_id: Connection identifier to remove
    """
    rate_limiter.remove_connection(connection_id)


async def check_message_rate_limit(connection_id: str) -> bool:
    """
    Check if connection can send another message.

    Args:
        connection_id: Connection identifier

    Returns:
        True if message allowed, False if rate limited

    Raises:
        WebSocketAuthError: If rate limited
    """
    rate_check = rate_limiter.check_message_rate(connection_id)
    if not rate_check.allowed:
        raise WebSocketAuthError(
            code=status.WS_1008_POLICY_VIOLATION, reason=rate_check.reason
        )

    return True


async def record_message(connection_id: str) -> bool:
    """
    Record a message from connection for rate limiting.

    Args:
        connection_id: Connection identifier

    Returns:
        True if message recorded successfully
    """
    return rate_limiter.record_message(connection_id)


def _extract_token_from_query(websocket: WebSocket) -> Optional[str]:
    """
    Extract JWT token from WebSocket query parameters.

    Args:
        websocket: WebSocket connection instance

    Returns:
        JWT token string or None if not found
    """
    query_string = websocket.url.query
    if not query_string:
        return None

    query_params = parse_qs(query_string)
    token_list = query_params.get("token", [])

    if not token_list:
        return None

    return token_list[0]


def _get_client_ip(websocket: WebSocket) -> str:
    """
    Get client IP address from WebSocket connection.

    Args:
        websocket: WebSocket connection instance

    Returns:
        Client IP address string
    """
    # Try to get real IP from headers (for proxy setups)
    forwarded_for = websocket.headers.get("x-forwarded-for")
    if forwarded_for:
        # Get first IP if multiple are present
        return forwarded_for.split(",")[0].strip()

    real_ip = websocket.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    # Fallback to direct client IP
    try:
        if websocket.client:
            return websocket.client.host
    except AttributeError:
        # WebSocket client not available yet (before accept)
        pass

    return "unknown"


# Development helpers
def create_demo_websocket_url(
    base_url: str, workstation_id: str, demo_user: str = "demo"
) -> str:
    """
    Create a WebSocket URL with demo token for development.

    Args:
        base_url: WebSocket base URL (e.g., "ws://localhost:8001")
        workstation_id: Workstation ID to connect to
        demo_user: Demo username

    Returns:
        Complete WebSocket URL with demo token
    """
    from .auth import create_demo_token

    demo_token = create_demo_token(user_id=demo_user, username=demo_user)
    return f"{base_url}/ws/{workstation_id}?token={demo_token}"
