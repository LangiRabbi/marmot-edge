"""
WebSocket manager for handling connections, subscriptions, and broadcasting.
Provides secure, scalable real-time communication for industrial monitoring.
"""

import asyncio
import json
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.core.auth import TokenData
from app.core.websocket_auth import (
    authenticate_websocket,
    authorize_workstation_access,
    check_connection_rate_limit,
    check_message_rate_limit,
    record_message,
    register_connection,
    unregister_connection,
    WebSocketAuthError
)
from app.schemas.websocket_messages import (
    ClientMessage,
    ServerMessage,
    SubscriptionType,
    MessageType,
    parse_client_message,
    create_error_message,
    ConnectedMessage,
    DisconnectedMessage,
    PongMessage
)


class ConnectionInfo:
    """Information about an active WebSocket connection."""

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        user: Optional[TokenData] = None
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user = user
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.subscriptions: Dict[str, Set[SubscriptionType]] = defaultdict(set)
        self.is_active = True

    def subscribe_to_workstation(self, workstation_id: str, subscription_types: List[SubscriptionType]):
        """Add subscriptions for a workstation."""
        for sub_type in subscription_types:
            if sub_type == SubscriptionType.ALL:
                # Subscribe to all types
                self.subscriptions[workstation_id] = {
                    SubscriptionType.DETECTIONS,
                    SubscriptionType.ZONES,
                    SubscriptionType.EFFICIENCY,
                    SubscriptionType.ALERTS
                }
            else:
                self.subscriptions[workstation_id].add(sub_type)

    def unsubscribe_from_workstation(
        self,
        workstation_id: str,
        subscription_types: Optional[List[SubscriptionType]] = None
    ):
        """Remove subscriptions for a workstation."""
        if workstation_id not in self.subscriptions:
            return

        if subscription_types is None:
            # Remove all subscriptions for this workstation
            del self.subscriptions[workstation_id]
        else:
            # Remove specific subscription types
            for sub_type in subscription_types:
                self.subscriptions[workstation_id].discard(sub_type)

            # Remove workstation if no subscriptions left
            if not self.subscriptions[workstation_id]:
                del self.subscriptions[workstation_id]

    def is_subscribed_to(self, workstation_id: str, message_type: SubscriptionType) -> bool:
        """Check if connection is subscribed to specific workstation and message type."""
        if workstation_id not in self.subscriptions:
            return False

        return message_type in self.subscriptions[workstation_id]

    def get_subscribed_workstations(self) -> Set[str]:
        """Get all workstation IDs this connection is subscribed to."""
        return set(self.subscriptions.keys())


class WebSocketManager:
    """
    Manages WebSocket connections, subscriptions, and message broadcasting.

    Features:
    - JWT authentication and authorization
    - Rate limiting and abuse prevention
    - Subscription-based message filtering
    - Connection health monitoring
    - Graceful error handling
    """

    def __init__(self):
        # Active connections
        self.connections: Dict[str, ConnectionInfo] = {}

        # Subscription tracking for efficient broadcasting
        self.workstation_subscribers: Dict[str, Dict[SubscriptionType, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )

        # Statistics
        self.total_connections = 0
        self.total_messages_sent = 0
        self.total_errors = 0

    async def connect(self, websocket: WebSocket, workstation_id: str) -> Optional[str]:
        """
        Handle new WebSocket connection.

        Args:
            websocket: WebSocket connection instance
            workstation_id: Initial workstation ID to connect to

        Returns:
            Connection ID if successful, None if rejected

        Raises:
            WebSocketDisconnect: If connection should be rejected
        """
        connection_id = str(uuid.uuid4())

        try:
            # Authenticate the connection
            user = await authenticate_websocket(websocket)

            # Check authorization for the workstation
            if not await authorize_workstation_access(user, workstation_id):
                await websocket.close(code=1008, reason="Access denied to workstation")
                return None

            # Check rate limits
            await check_connection_rate_limit(websocket, user)

            # Accept the connection
            await websocket.accept()

            # Register with rate limiter
            if not await register_connection(websocket, connection_id, user):
                await websocket.close(code=1008, reason="Rate limit exceeded")
                return None

            # Create connection info
            connection_info = ConnectionInfo(websocket, connection_id, user)
            self.connections[connection_id] = connection_info

            self.total_connections += 1

            # Send connection confirmation
            welcome_message = ConnectedMessage(
                connection_id=connection_id,
                features=["subscriptions", "rate_limiting", "authentication"]
            )
            await self._send_to_connection(connection_id, welcome_message)

            return connection_id

        except WebSocketAuthError as e:
            await websocket.close(code=e.code, reason=e.reason)
            return None
        except Exception as e:
            await websocket.close(code=1011, reason=f"Server error: {str(e)}")
            return None

    async def disconnect(self, connection_id: str, reason: str = "Client disconnect"):
        """
        Handle WebSocket disconnection.

        Args:
            connection_id: Connection identifier
            reason: Disconnection reason
        """
        if connection_id not in self.connections:
            return

        connection_info = self.connections[connection_id]

        try:
            # Send disconnection notification if connection is still active
            if connection_info.is_active:
                disconnect_message = DisconnectedMessage(reason=reason)
                await self._send_to_connection(connection_id, disconnect_message)
        except:
            pass  # Connection might already be closed

        # Remove from subscription tracking
        for workstation_id in connection_info.get_subscribed_workstations():
            for sub_type in SubscriptionType:
                self.workstation_subscribers[workstation_id][sub_type].discard(connection_id)

        # Clean up empty subscription sets
        self._cleanup_empty_subscriptions()

        # Remove connection (check if exists first)
        if connection_id in self.connections:
            del self.connections[connection_id]

        # Unregister from rate limiter
        await unregister_connection(connection_id)

        connection_info.is_active = False

    async def handle_message(self, connection_id: str, message_data: str):
        """
        Handle incoming message from client.

        Args:
            connection_id: Connection identifier
            message_data: Raw JSON message data
        """
        if connection_id not in self.connections:
            return

        connection_info = self.connections[connection_id]

        try:
            # Check rate limit for messages
            await check_message_rate_limit(connection_id)

            # Record the message
            await record_message(connection_id)

            # Parse message
            try:
                raw_data = json.loads(message_data)
                message = parse_client_message(raw_data)
            except (json.JSONDecodeError, ValidationError) as e:
                error_message = create_error_message(
                    "INVALID_MESSAGE",
                    f"Invalid message format: {str(e)}"
                )
                await self._send_to_connection(connection_id, error_message)
                return

            # Update last ping time
            connection_info.last_ping = datetime.utcnow()

            # Handle different message types
            if message.type == MessageType.SUBSCRIBE:
                await self._handle_subscribe(connection_id, message)
            elif message.type == MessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe(connection_id, message)
            elif message.type == MessageType.PING:
                await self._handle_ping(connection_id)

        except WebSocketAuthError as e:
            error_message = create_error_message("RATE_LIMIT", e.reason)
            await self._send_to_connection(connection_id, error_message)
            # Disconnect if rate limit violated
            await self.disconnect(connection_id, "Rate limit violation")

        except Exception as e:
            self.total_errors += 1
            error_message = create_error_message("SERVER_ERROR", f"Internal server error: {str(e)}")
            await self._send_to_connection(connection_id, error_message)

    async def broadcast_to_workstation(
        self,
        workstation_id: str,
        message: ServerMessage,
        subscription_type: SubscriptionType = SubscriptionType.ALL
    ):
        """
        Broadcast message to all subscribers of a workstation.

        Args:
            workstation_id: Target workstation ID
            message: Message to broadcast
            subscription_type: Type of subscription required to receive message
        """
        if subscription_type == SubscriptionType.ALL:
            # Send to all subscribers regardless of subscription type
            all_subscribers = set()
            for sub_type in SubscriptionType:
                if sub_type != SubscriptionType.ALL:
                    all_subscribers.update(
                        self.workstation_subscribers[workstation_id][sub_type]
                    )
            subscriber_ids = all_subscribers
        else:
            # Send to specific subscription type
            subscriber_ids = self.workstation_subscribers[workstation_id][subscription_type]

        # Send to all subscribers
        tasks = []
        for connection_id in subscriber_ids.copy():  # Copy to avoid modification during iteration
            if connection_id in self.connections:
                tasks.append(self._send_to_connection(connection_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _handle_subscribe(self, connection_id: str, message):
        """Handle subscription request."""
        connection_info = self.connections[connection_id]

        # Check authorization for each workstation
        authorized_workstations = []
        for workstation_id in message.workstation_ids:
            if await authorize_workstation_access(connection_info.user, workstation_id):
                authorized_workstations.append(workstation_id)

        if not authorized_workstations:
            error_message = create_error_message(
                "ACCESS_DENIED",
                "Access denied to all requested workstations"
            )
            await self._send_to_connection(connection_id, error_message)
            return

        # Add subscriptions
        for workstation_id in authorized_workstations:
            connection_info.subscribe_to_workstation(workstation_id, message.subscription_types)

            # Update subscription tracking
            for sub_type in message.subscription_types:
                if sub_type == SubscriptionType.ALL:
                    for actual_type in [SubscriptionType.DETECTIONS, SubscriptionType.ZONES,
                                      SubscriptionType.EFFICIENCY, SubscriptionType.ALERTS]:
                        self.workstation_subscribers[workstation_id][actual_type].add(connection_id)
                else:
                    self.workstation_subscribers[workstation_id][sub_type].add(connection_id)

    async def _handle_unsubscribe(self, connection_id: str, message):
        """Handle unsubscription request."""
        connection_info = self.connections[connection_id]

        workstation_ids = message.workstation_ids or list(connection_info.get_subscribed_workstations())

        for workstation_id in workstation_ids:
            # Remove from connection subscriptions
            connection_info.unsubscribe_from_workstation(workstation_id, message.subscription_types)

            # Remove from subscription tracking
            if message.subscription_types is None:
                # Remove all subscriptions
                for sub_type in SubscriptionType:
                    if sub_type != SubscriptionType.ALL:
                        self.workstation_subscribers[workstation_id][sub_type].discard(connection_id)
            else:
                for sub_type in message.subscription_types:
                    if sub_type == SubscriptionType.ALL:
                        for actual_type in [SubscriptionType.DETECTIONS, SubscriptionType.ZONES,
                                          SubscriptionType.EFFICIENCY, SubscriptionType.ALERTS]:
                            self.workstation_subscribers[workstation_id][actual_type].discard(connection_id)
                    else:
                        self.workstation_subscribers[workstation_id][sub_type].discard(connection_id)

        self._cleanup_empty_subscriptions()

    async def _handle_ping(self, connection_id: str):
        """Handle ping request."""
        pong_message = PongMessage()
        await self._send_to_connection(connection_id, pong_message)

    async def _send_to_connection(self, connection_id: str, message: ServerMessage):
        """Send message to specific connection."""
        if connection_id not in self.connections:
            return

        connection_info = self.connections[connection_id]

        try:
            message_json = message.json()
            await connection_info.websocket.send_text(message_json)
            self.total_messages_sent += 1
        except WebSocketDisconnect:
            # Connection closed, clean up
            await self.disconnect(connection_id, "Connection lost")
        except Exception as e:
            self.total_errors += 1
            # Try to disconnect gracefully
            try:
                await self.disconnect(connection_id, f"Send error: {str(e)}")
            except:
                pass

    def _cleanup_empty_subscriptions(self):
        """Remove empty subscription sets."""
        workstations_to_remove = []

        for workstation_id in list(self.workstation_subscribers.keys()):
            subscription_dict = self.workstation_subscribers[workstation_id]

            # Remove empty subscription types
            empty_types = [
                sub_type for sub_type, connections in subscription_dict.items()
                if not connections
            ]

            for sub_type in empty_types:
                del subscription_dict[sub_type]

            # Remove workstation if no subscriptions left
            if not subscription_dict:
                workstations_to_remove.append(workstation_id)

        for workstation_id in workstations_to_remove:
            del self.workstation_subscribers[workstation_id]

    def get_stats(self) -> dict:
        """Get WebSocket manager statistics."""
        active_connections = len(self.connections)

        # Count subscriptions by workstation
        workstation_counts = {}
        for workstation_id, subscription_dict in self.workstation_subscribers.items():
            total_subs = sum(len(connections) for connections in subscription_dict.values())
            workstation_counts[workstation_id] = total_subs

        return {
            "active_connections": active_connections,
            "total_connections_served": self.total_connections,
            "total_messages_sent": self.total_messages_sent,
            "total_errors": self.total_errors,
            "workstation_subscriptions": workstation_counts,
            "subscribed_workstations": len(self.workstation_subscribers)
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()