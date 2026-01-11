import asyncio
import logging
import time
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

import serial
from serial.tools import list_ports

import json
from pathlib import Path

import aiofiles

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ArduinoReading:
    rpm: float
    is_valid: bool = True
    timestamp: float = 0.0

    def to_dict(self):
        return {
            "rpm": self.rpm,
            "is_valid": self.is_valid,
            "timestamp": self.timestamp or time.time(),
        }


class ArduinoAdapter:
    """
    Adapter for reading sensor data from Arduino via Serial (USB).
    """

    def __init__(self, port: str = "COM3", baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self.retry_interval = 5.0

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
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
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
                line_bytes = self._serial.readline()
                if not line_bytes:
                    return None

                line = line_bytes.decode("utf-8").strip()

                if line:
                    # Parse JSON data from Arduino
                    try:
                        data = json.loads(line)
                        return ArduinoReading(
                            rpm=float(data.get("rpm", 0)),
                            is_valid=True,
                            timestamp=time.time(),
                        )
                    except json.JSONDecodeError:
                        # logger.warning(f"Invalid JSON/Line from Arduino: {line}")
                        return None

            return None

        except serial.SerialException as e:
            logger.error(f"Serial error reading from Arduino: {e}")
            self._connected = False
            return None
        except Exception as e:
            logger.error(f"Error reading from Arduino: {e}")
            return ArduinoReading(rpm=0, is_valid=False)

    def is_connected(self) -> bool:
        if self._serial is None:
            return False
        return self._connected and self._serial.is_open

    async def auto_reconnect(self) -> None:
        while True:
            if not self.is_connected():
                logger.info("Attempting to reconnect to Arduino...")
                await self.connect()
            await asyncio.sleep(self.retry_interval)

    def start_auto_reconnect(self) -> None:
        if self._reconnect_task is None:
            self._reconnect_task = asyncio.create_task(self.auto_reconnect())


class JsonDataAdapter:
    """
    Adapter for persisting readings to a JSON file.
    """

    def __init__(self, file_path: str = None):
        if file_path is None:
            data_dir = Path("data")
            file_path = str(data_dir / "readings.json")

        self.file_path = Path(file_path)
        self._lock = asyncio.Lock()
        self._buffer: List[dict] = []
        self._buffer_size = 10

    async def _ensure_file_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            async with aiofiles.open(self.file_path, "w") as f:
                await f.write("[]")

    async def append(self, reading: ArduinoReading) -> bool:
        try:
            async with self._lock:
                await self._ensure_file_exists()

                self._buffer.append(reading.to_dict())

                if len(self._buffer) >= self._buffer_size:
                    await self._flush_buffer()

                return True

        except Exception as e:
            logger.error(f"Error appending reading: {e}")
            return False

    async def _flush_buffer(self) -> None:
        if not self._buffer:
            return

        try:
            # Note: Reading and writing the whole file is inefficient for large datasets.
            # For a proper system, appending to a CSV or using a database is better.
            # Keeping JSON structure as requested.
            async with aiofiles.open(self.file_path, "r") as f:
                content = await f.read()
                data = json.loads(content) if content else []

            data.extend(self._buffer)

            async with aiofiles.open(self.file_path, "w") as f:
                await f.write(json.dumps(data, indent=2))

            self._buffer.clear()
            # logger.debug("Flushed to disk")

        except Exception as e:
            logger.error(f"Error flushing buffer: {e}")


class Main:
    def __init__(self):
        self.data_port = JsonDataAdapter()
        self.sensor_port = ArduinoAdapter()
        self.last_print_time = 0.0

    async def run(self):
        await self.sensor_port.connect()
        self.sensor_port.start_auto_reconnect()

        print("Starting Arduino Reader... Press Ctrl+C to stop.")

        try:
            while True:
                reading = await self.sensor_port.read()
                if reading and reading.is_valid:
                    await self.data_port.append(reading)

                    # Print to console every second
                    current_time = time.time()
                    if current_time - self.last_print_time >= 1.0:
                        print(
                            f"[{datetime.fromtimestamp(current_time).strftime('%H:%M:%S')}] RPM: {reading.rpm}"
                        )
                        self.last_print_time = current_time

                # Small sleep to yield control
                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            print("\nStopping...")
        finally:
            await self.sensor_port.disconnect()


if __name__ == "__main__":
    try:
        main = Main()
        asyncio.run(main.run())
    except KeyboardInterrupt:
        pass
