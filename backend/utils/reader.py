import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import serial
from serial.tools import list_ports

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "readings.jsonl"
PORT = "COM3"
BAUDRATE = 9600
TIMEOUT = 1.0


@dataclass
class ArduinoReading:
    rpm: float
    lift_force: float
    is_valid: bool = True
    timestamp: float = 0.0

    def to_json_line(self) -> str:
        """Convert to a single line JSON string"""
        return json.dumps(
            {
                "rpm": self.rpm,
                "lift_force": self.lift_force,
                "is_valid": self.is_valid,
                "timestamp": self.timestamp or time.time(),
            }
        )


def get_arduino_connection(port: str, baudrate: int) -> Optional[serial.Serial]:
    """Attempts to connect to the Arduino."""
    try:
        available_ports = [p.device for p in list_ports.comports()]
        logger.info(f"Available ports: {available_ports}")

        ser = serial.Serial(port=port, baudrate=baudrate, timeout=TIMEOUT)
        time.sleep(2.0)  # Wait for Arduino reset

        if ser.in_waiting:
            ser.read(ser.in_waiting)

        logger.info(f"Connected to {port}")
        return ser
    except serial.SerialException as e:
        logger.error(f"Failed to connect to {port}: {e}")
        return None


def save_reading(reading: ArduinoReading):
    """Appends a reading to the JSONL file."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "a") as f:
            f.write(reading.to_json_line() + "\n")
    except Exception as e:
        logger.error(f"Error saving data: {e}")


def main():
    ser: Optional[serial.Serial] = None
    last_print_time = 0.0

    print(f"Starting generic reader on {PORT}...")
    print("Press Ctrl+C to stop.")

    while True:
        try:
            # Reconnection Logic
            if ser is None or not ser.is_open:
                ser = get_arduino_connection(PORT, BAUDRATE)
                if not ser:
                    time.sleep(5)
                    continue

            # Read Line
            try:
                if ser.in_waiting:
                    line = ser.readline().decode("utf-8").strip()
                    if line:
                        try:
                            data = json.loads(line)
                            reading = ArduinoReading(
                                rpm=float(data.get("rpm", 0)),
                                lift_force=float(data.get("lift", 0)),
                                is_valid=True,
                                timestamp=time.time(),
                            )

                            # Save
                            save_reading(reading)

                            # Print every second
                            now = time.time()
                            if now - last_print_time >= 1.0:
                                print(
                                    f"[{datetime.fromtimestamp(now).strftime('%H:%M:%S')}] "
                                    f"RPM: {reading.rpm:.1f}, Lift: {reading.lift_force:.2f}"
                                )
                                last_print_time = now

                        except json.JSONDecodeError:
                            pass  # Ignore malformed lines

                else:
                    time.sleep(0.01)  # Prevent CPU hogging

            except serial.SerialException as e:
                logger.error(f"Serial connection lost: {e}")
                if ser:
                    ser.close()
                ser = None

        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(1)

    if ser and ser.is_open:
        ser.close()


if __name__ == "__main__":
    main()
