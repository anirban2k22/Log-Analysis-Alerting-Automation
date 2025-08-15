import random
import datetime
import uuid
import time
import os
import json

# --- Configuration ---
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
API_ENDPOINTS = ["/login", "/api/v1/users", "/api/v1/products", "/logout", "/health"]
STATUS_CODES = [200, 201, 202, 400, 401, 403, 404, 500, 503]

LOG_DIR = "logs"
RAW_LOG_FILE = os.path.join(LOG_DIR, "output.log")
JSON_LOG_FILE = os.path.join(LOG_DIR, "output.json.log")

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def generate_log_entry():
    """
    Generates a single, randomized log entry as a dictionary.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    request_id = str(uuid.uuid4())
    method = random.choice(HTTP_METHODS)
    api = random.choice(API_ENDPOINTS)
    status = random.choice(STATUS_CODES)
    latency = random.randint(10, 2000)

    log_entry = {
        "timestamp": timestamp,
        "request_id": request_id,
        "method": method,
        "api": api,
        "status": status,
        "latency_ms": latency
    }
    return log_entry

if __name__ == "__main__":
    print("Log generator started... Press Ctrl+C to stop.")
    try:
        with open(RAW_LOG_FILE, "a") as raw_f, open(JSON_LOG_FILE, "a") as json_f:
            while True:
                # Generate the log data
                log_data = generate_log_entry()

                # --- 1. Create and write the raw text log ---
                raw_log_line = (
                    f"[{log_data['timestamp']}] request_id={log_data['request_id']} "
                    f"method={log_data['method']} api={log_data['api']} "
                    f"status={log_data['status']} latency={log_data['latency_ms']}ms"
                )
                raw_f.write(raw_log_line + "\n")

                # --- 2. Create and write the JSON log ---
                json_log_line = json.dumps(log_data)
                json_f.write(json_log_line + "\n")

                # Print to console and flush files
                print(raw_log_line)
                raw_f.flush()
                json_f.flush()

                # Wait for a random interval before the next log
                time.sleep(random.uniform(0.5, 3.0))

    except KeyboardInterrupt:
        print("\nLog generator stopped.")