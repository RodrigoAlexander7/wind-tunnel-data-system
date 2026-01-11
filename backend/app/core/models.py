"""
Domain models for the Wind Tunnel Data Acquisition System.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SystemReading(BaseModel):
    """
    Represents a single reading from the wind tunnel system.
    This is the main data structure that gets persisted and transmitted.
    """

    timestamp: datetime = Field(default_factory=datetime.now)
    rpm: float = Field(default=0.0, ge=0, description="Propeller RPM from Arduino")
    lift_force: float = Field(
        default=0.0, description="Lift/Sustentation force in N from Arduino"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ArduinoReading(BaseModel):
    """
    Raw reading from Arduino sensors.
    """

    rpm: float = Field(default=0.0, ge=0)
    lift_force: float = Field(default=0.0)
    is_valid: bool = Field(default=True)


class SystemStatus(BaseModel):
    """
    Current status of the system for monitoring.
    """

    arduino_connected: bool = False
    websocket_clients: int = 0
    is_recording: bool = False
    readings_count: int = 0
