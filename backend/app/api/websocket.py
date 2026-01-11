"""
WebSocket endpoint for real-time data streaming.
"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


from app.core.models import SystemReading
from app.services.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    """
    WebSocket endpoint for bidirectional communication.

    Receives:
    - Control commands: {"type": "command", "action": "start_recording"|"stop_recording"|"clear"}

    Sends:
    - System readings: {"timestamp": "...", "rpm": 1500, "lift_force": 2.5}
    - Status updates: {"type": "status", ...}
    """
    # Import here to avoid circular imports
    from app.main import measurement_manager

    await connection_manager.connect(websocket)

    # Callback to send readings to this client
    async def send_reading(reading: SystemReading):
        try:
            await websocket.send_text(reading.model_dump_json())
        except Exception as e:
            logger.warning(f"Failed to send reading: {e}")

    # Subscribe to readings
    measurement_manager.subscribe(send_reading)

    # Send initial status
    status = measurement_manager.get_status()
    await connection_manager.send_personal(
        websocket, {"type": "status", "data": status.model_dump()}
    )

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type", "")

                if msg_type == "command":
                    action = message.get("action", "")

                    if action == "start_recording":
                        await measurement_manager.start_recording()
                        await connection_manager.send_personal(
                            websocket, {"type": "recording_started"}
                        )

                    elif action == "stop_recording":
                        await measurement_manager.stop_recording()
                        await connection_manager.send_personal(
                            websocket, {"type": "recording_stopped"}
                        )

                    elif action == "clear":
                        await measurement_manager.clear_readings()
                        await connection_manager.send_personal(
                            websocket, {"type": "readings_cleared"}
                        )

                    elif action == "get_status":
                        status = measurement_manager.get_status()
                        await connection_manager.send_personal(
                            websocket, {"type": "status", "data": status.model_dump()}
                        )

                elif msg_type == "ping":
                    await connection_manager.send_personal(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        measurement_manager.unsubscribe(send_reading)
        await connection_manager.disconnect(websocket)
