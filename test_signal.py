import signal
import sys
import time

def signal_handler(sig, frame):
    print("Caught signal")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("Running...")
while True:
    time.sleep(1)
