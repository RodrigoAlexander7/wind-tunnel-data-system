"""
Measurement Manager - Orchestrator for the data acquisition system.
Manages the reading loop, state, and data fusion.
"""

import asyncio
import logging
from datetime import datetime
from typing import Callable, List, Optional, Set

from app.core.config import settings
from app.core.models import ArduinoReading, SystemReading, SystemStatus
from app.ports.sensor_port import SensorPort
from app.ports.data_port import DataPort

logger = logging.getLogger(__name__)


class MeasurementManager:
    """
    Central orchestrator for the wind tunnel data acquisition system.

    Responsibilities:
    - Manage the reading loop from Arduino
    - Maintain current wind speed state (from frontend input)
    - Fuse data (Arduino readings + wind speed + timestamp)
    - Persist fused data
    - Notify subscribers (WebSocket clients) of new readings
    """

    def __init__(
        self,
        sensor: SensorPort,
        data_store: DataPort,
        reading_interval: float = settings.reading_interval,
    ):
        self.sensor = sensor
        self.data_store = data_store
        self.reading_interval = reading_interval

        # State
        self._is_running: bool = False
        self._is_recording: bool = False
        self._readings_count: int = 0

        # Subscribers for real-time updates
        self._subscribers: Set[Callable[[SystemReading], None]] = set()

        # Background task
        self._reading_task: Optional[asyncio.Task] = None

    def subscribe(self, callback: Callable[[SystemReading], None]) -> None:
        """
        Subscribe to receive new readings.
        """
        self._subscribers.add(callback)
        logger.debug(f"New subscriber added. Total: {len(self._subscribers)}")

    def unsubscribe(self, callback: Callable[[SystemReading], None]) -> None:
        """
        Unsubscribe from readings.
        """
        self._subscribers.discard(callback)
        logger.debug(f"Subscriber removed. Total: {len(self._subscribers)}")

    async def _notify_subscribers(self, reading: SystemReading) -> None:
        """
        Notify all subscribers of a new reading.
        """
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reading)
                else:
                    callback(reading)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

    async def start(self) -> None:
        """
        Start the measurement system.
        Connects to sensor and begins the reading loop.
        """
        if self._is_running:
            logger.warning("Measurement manager already running")
            return

        # Connect to sensor
        connected = await self.sensor.connect()
        if not connected:
            logger.warning("Failed to connect to sensor, will retry in background")

        # Start reading loop
        self._is_running = True
        self._reading_task = asyncio.create_task(self._reading_loop())
        logger.info("Measurement manager started")

    async def stop(self) -> None:
        """
        Stop the measurement system.
        """
        self._is_running = False

        if self._reading_task:
            self._reading_task.cancel()
            try:
                await self._reading_task
            except asyncio.CancelledError:
                pass
            self._reading_task = None

        await self.sensor.disconnect()

        # Flush any buffered data
        if hasattr(self.data_store, "flush"):
            await self.data_store.flush()

        logger.info("Measurement manager stopped")

    async def start_recording(self) -> None:
        """
        Start recording data to persistent storage.
        """
        self._is_recording = True
        self._readings_count = 0
        logger.info("Recording started")

    async def stop_recording(self) -> None:
        """
        Stop recording and flush data.
        """
        self._is_recording = False
        if hasattr(self.data_store, "flush"):
            await self.data_store.flush()
        logger.info(f"Recording stopped. Total readings: {self._readings_count}")

    async def _reading_loop(self) -> None:
        """
        Main reading loop that runs continuously.
        """
        reconnect_interval = settings.serial_retry_interval

        while self._is_running:
            try:
                # Check sensor connection
                if not self.sensor.is_connected():
                    logger.info(
                        f"Sensor disconnected, retrying in {reconnect_interval}s..."
                    )
                    await asyncio.sleep(reconnect_interval)
                    await self.sensor.connect()
                    continue

                # Read from sensor
                arduino_reading = await self.sensor.read()

                if arduino_reading and arduino_reading.is_valid:
                    # Fuse data: Arduino reading + timestamp
                    fused_reading = SystemReading(
                        timestamp=datetime.now(),
                        rpm=arduino_reading.rpm,
                        lift_force=arduino_reading.lift_force,
                    )

                    # Persist if recording
                    if self._is_recording:
                        await self.data_store.append(fused_reading)
                        self._readings_count += 1

                    # Notify subscribers (WebSocket clients)
                    await self._notify_subscribers(fused_reading)

                # Wait for next reading cycle
                await asyncio.sleep(self.reading_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reading loop: {e}")
                await asyncio.sleep(1.0)  # Brief pause on error

    def get_status(self) -> SystemStatus:
        """
        Get current system status.
        """
        return SystemStatus(
            arduino_connected=self.sensor.is_connected(),
            websocket_clients=len(self._subscribers),
            is_recording=self._is_recording,
            readings_count=self._readings_count,
        )

    async def get_recent_readings(self, count: int = 100) -> List[SystemReading]:
        """
        Get recent readings from storage.
        """
        return await self.data_store.get_recent(count)

    async def clear_readings(self) -> bool:
        """
        Clear all stored readings.
        """
        self._readings_count = 0
        return await self.data_store.clear()
