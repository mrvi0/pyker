#!/usr/bin/env python3
"""Demo bot for trying Pyker locally."""

import os
import sys
import time
import random
from datetime import datetime


def main() -> None:
    print(f"[{datetime.now()}] Bot started (PID: {os.getpid()})")
    counter = 0
    while True:
        try:
            counter += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if counter % 10 == 0:
                print(f"[{now}] Completed {counter} iterations")
            if random.random() < 0.001:
                raise RuntimeError("demo random error")
            time.sleep(1)
        except KeyboardInterrupt:
            print(f"[{datetime.now()}] Stopped by signal")
            break
        except Exception as exc:
            print(f"[{datetime.now()}] Error: {exc}")
            time.sleep(5)
    print(f"[{datetime.now()}] Bot finished")


if __name__ == "__main__":
    main()
    sys.exit(0)
