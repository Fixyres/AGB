import sys
import time

def log(message: str, level: str = "INFO") -> None:
    sys.stdout.write('\r' + f"[{time.strftime("%H:%M:%S")}] [{level}] {message}")
    sys.stdout.flush()