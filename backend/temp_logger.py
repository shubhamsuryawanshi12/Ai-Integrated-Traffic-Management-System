
# Log file location
import os
LOG_FILE = r"D:\Hackathon\backend\server_debug.log"

def log_msg(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now().isoformat()} - {msg}\n")
    except:
        pass
