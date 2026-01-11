"""
REST API endpoints for system control and data retrieval.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException


from app.core.models import SystemReading, SystemStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/status", response_model=SystemStatus)
async def get_status():
    """
    Get current system status.
    """
    from app.main import measurement_manager

    return measurement_manager.get_status()


@router.get("/readings", response_model=List[SystemReading])
async def get_readings(limit: int = 100):
    """
    Get recent readings from storage.
    """
    from app.main import measurement_manager

    return await measurement_manager.get_recent_readings(limit)


@router.post("/recording/start")
async def start_recording():
    """
    Start recording data to file.
    """
    from app.main import measurement_manager

    await measurement_manager.start_recording()
    return {"status": "recording_started"}


@router.post("/recording/stop")
async def stop_recording():
    """
    Stop recording data.
    """
    from app.main import measurement_manager

    await measurement_manager.stop_recording()
    return {"status": "recording_stopped"}


@router.delete("/readings")
async def clear_readings():
    """
    Clear all stored readings.
    """
    from app.main import measurement_manager

    success = await measurement_manager.clear_readings()
    if success:
        return {"status": "cleared"}
    raise HTTPException(status_code=500, detail="Failed to clear readings")


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    from app.main import measurement_manager

    status = measurement_manager.get_status()
    return {
        "status": "healthy",
        "arduino_connected": status.arduino_connected,
        "websocket_clients": status.websocket_clients,
    }
