"""
Arduino Serial Adapter - Reads RPM and Lift Force from Arduino via USB Serial.
"""
import asyncio
import logging
from typing import Optional

import serial
from serial.tools import list_ports

from app.core.config import settings
from app.core.models import ArduinoReading
from app.ports.sensor_port import SensorPort

logger = logging.getLogger(__name__)


class ArduinoAdapter(SensorPort):
    """
    Adapter for reading sensor data from Arduino via Serial (USB).
    
    Expected Arduino data format (JSON per line):
    {"rpm": 1500.0, "lift": 2.5}
    """
    
    def __init__(
        self,
        port: str = settings.serial_port,
        baudrate: int = settings.serial_baudrate,
        timeout: float = settings.serial_timeout
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """
        Establish connection to Arduino via Serial port.
        """
        try:
            # List available ports for debugging
            available_ports = [p.device for p in list_ports.comports()]
            logger.info(f"Available serial ports: {available_ports}")
            
            # Try to connect
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Wait for Arduino to reset after connection
            await asyncio.sleep(2.0)
            
            # Clear any pending data
            if self._serial.in_waiting:
                self._serial.read(self._serial.in_waiting)
            
            self._connected = True
            logger.info(f"Connected to Arduino on {self.port}")
            return True
            
        except serial.SerialException as e:
            logger.warning(f"Failed to connect to Arduino on {self.port}: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Arduino: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """
        Close the Serial connection.
        """
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
            
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Disconnected from Arduino")
        
        self._connected = False
    
    async def read(self) -> Optional[ArduinoReading]:
        """
        Read RPM and Lift Force from Arduino.
        Expected format: {"rpm": float, "lift": float}
        """
        if not self._connected or not self._serial:
            return None
        
        try:
            if self._serial.in_waiting:
                # Read a line from Serial
                line = self._serial.readline().decode('utf-8').strip()
                
                if line:
                    # Log raw data received from Arduino
                    logger.info(f"Raw data from Arduino: {line}")
                    
                    # Parse JSON data from Arduino
                    import json
                    data = json.loads(line)
                    
                    return ArduinoReading(
                        rpm=float(data.get('rpm', 0)),
                        lift_force=float(data.get('lift', 0)),
                        is_valid=True
                    )
            
            
            return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from Arduino: {e}")
            return ArduinoReading(is_valid=False)
        except serial.SerialException as e:
            logger.error(f"Serial error reading from Arduino: {e}")
            self._connected = False
            return None
        except Exception as e:
            logger.error(f"Error reading from Arduino: {e}")
            return ArduinoReading(is_valid=False)
    
    def is_connected(self) -> bool:
        """
        Check if Arduino is currently connected.
        """
        if self._serial is None:
            return False
        return self._connected and self._serial.is_open
    
    async def auto_reconnect(self, interval: float = settings.serial_retry_interval) -> None:
        """
        Background task that attempts to reconnect if connection is lost.
        """
        while True:
            if not self.is_connected():
                logger.info("Attempting to reconnect to Arduino...")
                await self.connect()
            await asyncio.sleep(interval)
    
    def start_auto_reconnect(self) -> None:
        """
        Start the auto-reconnect background task.
        """
        if self._reconnect_task is None:
            self._reconnect_task = asyncio.create_task(self.auto_reconnect())
