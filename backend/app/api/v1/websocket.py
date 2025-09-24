"""
WebSocket endpoints for real-time communication.
Provides secure, authenticated WebSocket connections for industrial monitoring.
"""

import json

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.core.rate_limiting import rate_limiter
from app.services.websocket_manager import websocket_manager

router = APIRouter()


@router.websocket("/ws/{workstation_id}")
async def websocket_endpoint(websocket: WebSocket, workstation_id: str):
    """
    WebSocket endpoint for real-time workstation monitoring.

    URL Format: ws://localhost:8001/api/v1/ws/{workstation_id}?token={jwt_token}

    Authentication:
    - JWT token required in query parameter: ?token=<jwt_token>
    - Token must have access to the specified workstation

    Message Types:
    - subscribe: Subscribe to workstation updates
    - unsubscribe: Unsubscribe from updates
    - ping: Connection health check

    Example Usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8001/api/v1/ws/workstation_001?token=<jwt>');

    // Subscribe to all updates
    ws.send(JSON.stringify({
        type: 'subscribe',
        workstation_ids: ['workstation_001'],
        subscription_types: ['all']
    }));
    ```
    """
    print(f"[WebSocket] Connection attempt for workstation: {workstation_id}")
    print(f"[WebSocket] Headers: {dict(websocket.headers)}")
    print(f"[WebSocket] Query params: {dict(websocket.query_params)}")
    from app.core.websocket_auth import WEBSOCKET_AUTH_REQUIRED

    print(f"[WebSocket] Auth required: {WEBSOCKET_AUTH_REQUIRED}")

    connection_id = None

    try:
        # Connect and authenticate
        connection_id = await websocket_manager.connect(websocket, workstation_id)

        if connection_id is None:
            # Connection was rejected (auth/rate limit failure)
            return

        # Handle messages
        while True:
            try:
                # Receive message from client
                message_data = await websocket.receive_text()
                print(
                    f"[WebSocket API] Received message on websocket endpoint: {message_data}"
                )

                # Handle the message
                print(
                    f"[WebSocket API] Calling websocket_manager.handle_message for connection {connection_id}"
                )
                await websocket_manager.handle_message(connection_id, message_data)

            except WebSocketDisconnect:
                break
            except Exception as e:
                # Log error but continue listening
                print(f"Error handling WebSocket message: {e}")
                # Send error to client if possible
                try:
                    error_response = {
                        "type": "error",
                        "error_code": "MESSAGE_ERROR",
                        "error_message": str(e),
                    }
                    await websocket.send_text(json.dumps(error_response))
                except:
                    # If we can't send error, connection is probably broken
                    break

    except WebSocketDisconnect:
        pass  # Normal disconnection
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(connection_id, "Connection ended")


@router.get("/websocket/health")
async def websocket_health():
    """
    WebSocket service health check endpoint.

    Returns current statistics and service status.
    """
    try:
        # Get WebSocket manager stats
        ws_stats = websocket_manager.get_stats()

        # Get rate limiter stats
        rate_stats = rate_limiter.get_stats()

        # Combine stats
        health_data = {
            "status": "healthy",
            "websocket": ws_stats,
            "rate_limiting": rate_stats,
            "features": {
                "authentication": True,
                "rate_limiting": True,
                "subscriptions": True,
                "monitoring": True,
            },
        }

        return health_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/websocket/demo")
async def websocket_demo():
    """
    Demo page for testing WebSocket connections.

    Provides a simple HTML interface for testing WebSocket functionality.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Demo - Marmot Industrial Monitoring</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ccc; border-radius: 5px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 3px; }
            .connected { background-color: #d4edda; color: #155724; }
            .disconnected { background-color: #f8d7da; color: #721c24; }
            .messages { height: 300px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; background: #f9f9f9; }
            input[type="text"] { width: 200px; padding: 5px; }
            button { padding: 8px 15px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .message { margin: 5px 0; padding: 5px; }
            .sent { background: #e3f2fd; }
            .received { background: #f3e5f5; }
            .error { background: #ffebee; color: #c62828; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 WebSocket Demo - Industrial Monitoring</h1>

            <div class="section">
                <h3>Connection</h3>
                <div id="status" class="status disconnected">Disconnected</div>
                <input type="text" id="workstationId" placeholder="workstation_001" value="workstation_001">
                <input type="text" id="token" placeholder="JWT Token (optional for demo)">
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <button onclick="getDemoToken()">Get Demo Token</button>
            </div>

            <div class="section">
                <h3>Quick Actions</h3>
                <button onclick="subscribe()">Subscribe to All</button>
                <button onclick="subscribeDetections()">Subscribe Detections Only</button>
                <button onclick="unsubscribe()">Unsubscribe</button>
                <button onclick="ping()">Ping</button>
            </div>

            <div class="section">
                <h3>Custom Message</h3>
                <textarea id="customMessage" rows="3" cols="50" placeholder='{"type": "ping"}'></textarea><br>
                <button onclick="sendCustom()">Send Custom Message</button>
            </div>

            <div class="section">
                <h3>Messages</h3>
                <button onclick="clearMessages()">Clear Messages</button>
                <div id="messages" class="messages"></div>
            </div>
        </div>

        <script>
            let ws = null;

            function addMessage(content, type = 'info') {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = `message ${type}`;
                div.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${content}`;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }

            function updateStatus(connected) {
                const status = document.getElementById('status');
                if (connected) {
                    status.textContent = 'Connected';
                    status.className = 'status connected';
                } else {
                    status.textContent = 'Disconnected';
                    status.className = 'status disconnected';
                }
            }

            function connect() {
                const workstationId = document.getElementById('workstationId').value || 'workstation_001';
                const token = document.getElementById('token').value;

                let url = `ws://localhost:8001/api/v1/ws/${workstationId}`;
                if (token) {
                    url += `?token=${token}`;
                }

                try {
                    ws = new WebSocket(url);

                    ws.onopen = function(event) {
                        updateStatus(true);
                        addMessage('WebSocket connected!', 'received');
                    };

                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        addMessage(`Received: ${JSON.stringify(data, null, 2)}`, 'received');
                    };

                    ws.onclose = function(event) {
                        updateStatus(false);
                        addMessage(`WebSocket closed. Code: ${event.code}, Reason: ${event.reason}`, 'error');
                    };

                    ws.onerror = function(error) {
                        addMessage(`WebSocket error: ${error}`, 'error');
                    };

                } catch (error) {
                    addMessage(`Connection error: ${error}`, 'error');
                }
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
                updateStatus(false);
            }

            function sendMessage(message) {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('Not connected to WebSocket', 'error');
                    return;
                }

                const messageStr = JSON.stringify(message);
                ws.send(messageStr);
                addMessage(`Sent: ${messageStr}`, 'sent');
            }

            function subscribe() {
                sendMessage({
                    type: 'subscribe',
                    workstation_ids: [document.getElementById('workstationId').value || 'workstation_001'],
                    subscription_types: ['all']
                });
            }

            function subscribeDetections() {
                sendMessage({
                    type: 'subscribe',
                    workstation_ids: [document.getElementById('workstationId').value || 'workstation_001'],
                    subscription_types: ['detections']
                });
            }

            function unsubscribe() {
                sendMessage({
                    type: 'unsubscribe'
                });
            }

            function ping() {
                sendMessage({
                    type: 'ping'
                });
            }

            function sendCustom() {
                const customText = document.getElementById('customMessage').value;
                if (!customText.trim()) {
                    addMessage('Enter a custom message', 'error');
                    return;
                }

                try {
                    const message = JSON.parse(customText);
                    sendMessage(message);
                } catch (error) {
                    addMessage(`Invalid JSON: ${error}`, 'error');
                }
            }

            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }

            async function getDemoToken() {
                try {
                    const response = await fetch('/api/v1/websocket/demo-token');
                    const data = await response.json();
                    document.getElementById('token').value = data.token;
                    addMessage('Demo token generated!', 'received');
                } catch (error) {
                    addMessage(`Failed to get demo token: ${error}`, 'error');
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/websocket/demo-token")
async def get_demo_token():
    """
    Generate a demo JWT token for testing WebSocket connections.

    ⚠️ Only use in development! Remove in production.
    """
    try:
        from app.core.auth import create_demo_token

        # Create demo token with access to all workstations
        demo_token = create_demo_token(
            user_id="demo_user",
            username="demo",
            workstation_ids=["*"],  # Access to all workstations
        )

        return {
            "token": demo_token,
            "user": "demo",
            "workstation_access": "all",
            "expires_in_minutes": 30,
            "note": "Demo token for development only",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create demo token: {str(e)}"
        )


@router.post("/websocket/broadcast")
async def broadcast_test_message(
    workstation_id: str, message_type: str = "test", content: str = "Test message"
):
    """
    Test endpoint for broadcasting messages to WebSocket subscribers.

    ⚠️ Development/testing only!
    """
    try:
        # Move all imports to top level to avoid scope issues
        import json
        from datetime import datetime

        from app.schemas.websocket_messages import (
            AlertLevel,
            AlertMessage,
            PersonDetection,
            SubscriptionType,
            create_detection_update,
        )

        print(f"[BROADCAST DEBUG] Received request:")
        print(f"  workstation_id: {workstation_id}")
        print(f"  message_type: {message_type}")
        print(f"  content: {content[:200]}...")

        # Check if content is a valid detection update JSON
        if message_type == "detection_update":
            print(f"[BROADCAST DEBUG] Processing detection_update message")

            # Parse detection data from content
            detection_data = json.loads(content)
            print(f"[BROADCAST DEBUG] Parsed detection_data: {detection_data}")

            # Create PersonDetection objects
            persons = [
                PersonDetection(**person_data)
                for person_data in detection_data.get("persons", [])
            ]
            print(f"[BROADCAST DEBUG] Created {len(persons)} PersonDetection objects")

            # Handle frame timestamp with proper default value
            frame_timestamp_str = detection_data.get("frame_timestamp")
            if frame_timestamp_str:
                frame_timestamp = datetime.fromisoformat(frame_timestamp_str)
            else:
                frame_timestamp = datetime.now()

            # Create proper DetectionUpdateMessage
            test_message = create_detection_update(
                workstation_id=workstation_id,
                frame_timestamp=frame_timestamp,
                persons=persons,
                processing_fps=detection_data.get("processing_fps", 15.0),
                frame_number=detection_data.get("frame_number", 0),
            )
            print(f"[BROADCAST DEBUG] Created DetectionUpdateMessage: {test_message}")
            print(f"[BROADCAST DEBUG] Message type: {test_message.type}")

            subscription_type = SubscriptionType.DETECTIONS
            print(f"[BROADCAST DEBUG] Using subscription_type: {subscription_type}")

        else:
            # Create test alert message for non-detection types
            test_message = AlertMessage(
                workstation_id=workstation_id,
                alert_type=message_type,
                level=AlertLevel.INFO,
                title="Test Alert",
                message=content,
                data={"test": True},
            )
            subscription_type = SubscriptionType.ALERTS

        # Broadcast to subscribers
        print(f"[BROADCAST DEBUG] About to broadcast message:")
        print(f"  workstation_id: {workstation_id}")
        print(f"  message: {test_message}")
        print(f"  subscription_type: {subscription_type}")

        await websocket_manager.broadcast_to_workstation(
            workstation_id=workstation_id,
            message=test_message,
            subscription_type=subscription_type,
        )

        print(f"[BROADCAST DEBUG] Broadcast completed")

        return {
            "success": True,
            "message": f"Test message broadcasted to workstation {workstation_id}",
            "subscribers": len(
                websocket_manager.workstation_subscribers.get(workstation_id, {})
            ),
        }

    except Exception as e:
        print(f"[BROADCAST DEBUG] FATAL EXCEPTION: {e}")
        import traceback

        print(f"[BROADCAST DEBUG] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")


@router.post("/websocket/broadcast-detection")
async def broadcast_detection_message(
    workstation_id: str,
    bbox1_x1: float = 0.2,
    bbox1_y1: float = 0.3,
    bbox1_x2: float = 0.4,
    bbox1_y2: float = 0.7,
    bbox2_x1: float = 0.6,
    bbox2_y1: float = 0.2,
    bbox2_x2: float = 0.8,
    bbox2_y2: float = 0.6,
):
    """
    Test endpoint for broadcasting detection messages with bounding boxes to WebSocket subscribers.

    ⚠️ Development/testing only!
    """
    try:
        from datetime import datetime

        from app.schemas.websocket_messages import (
            PersonDetection,
            SubscriptionType,
            create_detection_update,
        )

        # Create mock persons with customizable bounding boxes
        mock_persons = [
            PersonDetection(
                tracking_id=1,
                bbox=[bbox1_x1, bbox1_y1, bbox1_x2, bbox1_y2],
                center=[(bbox1_x1 + bbox1_x2) / 2, (bbox1_y1 + bbox1_y2) / 2],
                confidence=0.89,
                zones=["zone_1"],
            ),
            PersonDetection(
                tracking_id=2,
                bbox=[bbox2_x1, bbox2_y1, bbox2_x2, bbox2_y2],
                center=[(bbox2_x1 + bbox2_x2) / 2, (bbox2_y1 + bbox2_y2) / 2],
                confidence=0.92,
                zones=["zone_2"],
            ),
        ]

        # Create detection message
        detection_message = create_detection_update(
            workstation_id=workstation_id,
            frame_timestamp=datetime.now(),
            persons=mock_persons,
            processing_fps=15.3,
            frame_number=12345,
        )

        # Broadcast to subscribers using the SAME websocket_manager instance as main app
        await websocket_manager.broadcast_to_workstation(
            workstation_id=workstation_id,
            message=detection_message,
            subscription_type=SubscriptionType.DETECTIONS,
        )

        return {
            "success": True,
            "message": f"Detection message broadcasted to workstation {workstation_id}",
            "subscribers": len(
                websocket_manager.workstation_subscribers.get(workstation_id, {})
            ),
            "detection_data": {
                "person_count": len(mock_persons),
                "bounding_boxes": [
                    {"id": 1, "bbox": [bbox1_x1, bbox1_y1, bbox1_x2, bbox1_y2]},
                    {"id": 2, "bbox": [bbox2_x1, bbox2_y1, bbox2_x2, bbox2_y2]},
                ],
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Detection broadcast failed: {str(e)}"
        )


@router.post("/websocket/clear-connections")
async def clear_all_connections():
    """
    Clear all WebSocket connections from rate limiter.

    ⚠️ Development/debugging only!
    """
    try:
        from app.core.rate_limiting import rate_limiter

        rate_limiter.clear_all_connections()

        return {"success": True, "message": "All connections cleared from rate limiter"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")
