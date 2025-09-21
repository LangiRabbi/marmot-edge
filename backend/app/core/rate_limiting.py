"""
Rate limiting system for WebSocket connections and messages.
Prevents abuse and ensures system stability under high load.
"""

import asyncio
import os
import time
from collections import defaultdict, deque
from typing import Dict, Optional

from pydantic import BaseModel

# Configuration from environment
MAX_CONNECTIONS_PER_IP = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS_PER_IP", "5"))
MESSAGE_RATE_LIMIT = int(os.getenv("WEBSOCKET_MESSAGE_RATE_LIMIT", "100"))
RATE_LIMIT_WINDOW = 60  # 1 minute window
CLEANUP_INTERVAL = 300  # 5 minutes


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""
    connection_id: str
    ip_address: str
    user_id: Optional[str] = None
    connected_at: float
    last_message: float
    message_count: int = 0


class RateLimitResult(BaseModel):
    """Result of rate limit check."""
    allowed: bool
    reason: Optional[str] = None
    retry_after: Optional[int] = None


class RateLimiter:
    """
    Rate limiter for WebSocket connections and messages.

    Features:
    - Connection limit per IP address
    - Message rate limiting per connection
    - Automatic cleanup of old records
    - Thread-safe operations
    """

    def __init__(self):
        # Connection tracking
        self.connections: Dict[str, ConnectionInfo] = {}  # connection_id -> info
        self.connections_by_ip: Dict[str, set] = defaultdict(set)  # ip -> connection_ids

        # Message rate tracking (sliding window)
        self.message_times: Dict[str, deque] = defaultdict(deque)  # connection_id -> timestamps

        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the rate limiter and cleanup task."""
        if self._running:
            return

        self._running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the rate limiter and cleanup task."""
        self._running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

    def check_connection_limit(self, ip_address: str) -> RateLimitResult:
        """
        Check if IP address can create new connection.

        Args:
            ip_address: Client IP address

        Returns:
            RateLimitResult indicating if connection is allowed
        """
        current_connections = len(self.connections_by_ip[ip_address])

        if current_connections >= MAX_CONNECTIONS_PER_IP:
            return RateLimitResult(
                allowed=False,
                reason=f"Too many connections from IP {ip_address}: {current_connections}/{MAX_CONNECTIONS_PER_IP}",
                retry_after=60
            )

        return RateLimitResult(allowed=True)

    def add_connection(self, connection_id: str, ip_address: str, user_id: Optional[str] = None) -> bool:
        """
        Add a new connection to tracking.

        Args:
            connection_id: Unique connection identifier
            ip_address: Client IP address
            user_id: User ID if authenticated

        Returns:
            True if connection was added, False if rate limited
        """
        # Check rate limit first
        rate_check = self.check_connection_limit(ip_address)
        if not rate_check.allowed:
            return False

        # Add connection
        now = time.time()
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            ip_address=ip_address,
            user_id=user_id,
            connected_at=now,
            last_message=now
        )

        self.connections[connection_id] = connection_info
        self.connections_by_ip[ip_address].add(connection_id)

        return True

    def remove_connection(self, connection_id: str):
        """
        Remove connection from tracking.

        Args:
            connection_id: Connection identifier to remove
        """
        if connection_id not in self.connections:
            return

        connection_info = self.connections[connection_id]
        ip_address = connection_info.ip_address

        # Remove from all tracking structures
        del self.connections[connection_id]
        self.connections_by_ip[ip_address].discard(connection_id)

        # Clean up empty IP sets
        if not self.connections_by_ip[ip_address]:
            del self.connections_by_ip[ip_address]

        # Remove message history
        if connection_id in self.message_times:
            del self.message_times[connection_id]

    def check_message_rate(self, connection_id: str) -> RateLimitResult:
        """
        Check if connection can send another message.

        Args:
            connection_id: Connection identifier

        Returns:
            RateLimitResult indicating if message is allowed
        """
        if connection_id not in self.connections:
            return RateLimitResult(
                allowed=False,
                reason="Connection not found"
            )

        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW

        # Get message times for this connection
        message_times = self.message_times[connection_id]

        # Remove old messages outside the window
        while message_times and message_times[0] < window_start:
            message_times.popleft()

        # Check rate limit
        if len(message_times) >= MESSAGE_RATE_LIMIT:
            return RateLimitResult(
                allowed=False,
                reason=f"Message rate limit exceeded: {len(message_times)}/{MESSAGE_RATE_LIMIT} per minute",
                retry_after=int(message_times[0] + RATE_LIMIT_WINDOW - now) + 1
            )

        return RateLimitResult(allowed=True)

    def record_message(self, connection_id: str) -> bool:
        """
        Record a message from connection.

        Args:
            connection_id: Connection identifier

        Returns:
            True if message was recorded, False if rate limited
        """
        # Check rate limit
        rate_check = self.check_message_rate(connection_id)
        if not rate_check.allowed:
            return False

        # Record the message
        now = time.time()
        self.message_times[connection_id].append(now)

        # Update connection info
        if connection_id in self.connections:
            self.connections[connection_id].last_message = now
            self.connections[connection_id].message_count += 1

        return True

    def get_stats(self) -> dict:
        """
        Get current rate limiter statistics.

        Returns:
            Dictionary with current statistics
        """
        total_connections = len(self.connections)
        connections_by_ip = {ip: len(conn_ids) for ip, conn_ids in self.connections_by_ip.items()}

        # Calculate message rates
        now = time.time()
        window_start = now - 60  # Last minute

        total_messages_last_minute = 0
        for message_times in self.message_times.values():
            total_messages_last_minute += sum(1 for t in message_times if t >= window_start)

        return {
            "total_connections": total_connections,
            "connections_by_ip": connections_by_ip,
            "max_connections_per_ip": MAX_CONNECTIONS_PER_IP,
            "message_rate_limit": MESSAGE_RATE_LIMIT,
            "messages_last_minute": total_messages_last_minute,
            "avg_messages_per_connection": (
                total_messages_last_minute / total_connections
                if total_connections > 0 else 0
            )
        }

    def auto_disconnect_violators(self) -> list[str]:
        """
        Identify connections that should be disconnected due to violations.

        Returns:
            List of connection IDs to disconnect
        """
        to_disconnect = []
        now = time.time()

        for connection_id, connection_info in self.connections.items():
            # Check for inactive connections (no message in last 5 minutes)
            if now - connection_info.last_message > 300:
                to_disconnect.append(connection_id)
                continue

            # Check message rate violations
            rate_check = self.check_message_rate(connection_id)
            if not rate_check.allowed:
                to_disconnect.append(connection_id)

        return to_disconnect

    async def _cleanup_loop(self):
        """Periodic cleanup of old connection data."""
        while self._running:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL)

                # Clean up old message times
                now = time.time()
                window_start = now - RATE_LIMIT_WINDOW

                for connection_id in list(self.message_times.keys()):
                    message_times = self.message_times[connection_id]

                    # Remove old messages
                    while message_times and message_times[0] < window_start:
                        message_times.popleft()

                    # Remove empty deques for disconnected connections
                    if not message_times and connection_id not in self.connections:
                        del self.message_times[connection_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Rate limiter cleanup error: {e}")


# Global rate limiter instance
rate_limiter = RateLimiter()