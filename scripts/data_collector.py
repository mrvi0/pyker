#!/usr/bin/env python3
"""Demo data collector for trying Pyker locally."""

import json
import time
import random
from datetime import datetime
from pathlib import Path


def collect_data() -> dict:
    return {
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(20, 30), 2),
        "humidity": round(random.uniform(40, 80), 2),
        "pressure": round(random.uniform(1000, 1020), 2),
    }


def save_data(data: dict, filename: str = "collected_data.json") -> int:
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(exist_ok=True)
    file_path = data_dir / filename

    existing = []
    if file_path.exists():
        try:
            existing = json.loads(file_path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except (OSError, json.JSONDecodeError):
            existing = []

    existing.append(data)
    file_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return len(existing)


def main() -> None:
    print(f"[{datetime.now()}] Data collector started")
    counter = 0
    while True:
        try:
            counter += 1
            count = save_data(collect_data())
            if counter % 5 == 0:
                print(f"[{datetime.now()}] Saved {count} records")
            time.sleep(2)
        except KeyboardInterrupt:
            print(f"[{datetime.now()}] Stopped by signal")
            break


if __name__ == "__main__":
    main()
