import random
import datetime
import uuid
import time
import os
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Configuration ---
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
API_ENDPOINTS = ["/login", "/api/v1/users", "/api/v1/products", "/logout", "/health"]
STATUS_CODES = [200, 201, 202, 400, 401, 403, 404, 500, 503]

LOG_DIR = "logs"
RAW_LOG_FILE = os.path.join(LOG_DIR, "output.log")
JSON_LOG_FILE = os.path.join(LOG_DIR, "output.json.log")

# InfluxDB Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "my-super-secret-token"
INFLUXDB_ORG = "my-org"
INFLUXDB_BUCKET = "my-bucket"

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def generate_log_entry():
    """
    Generates a single, randomized log entry as a dictionary.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    request_id = str(uuid.uuid4())
    method = random.choice(HTTP_METHODS)
    api = random.choice(API_ENDPOINTS)
    status = random.choice(STATUS_CODES)
    latency = random.randint(10, 2000)

    log_entry = {
        "timestamp": timestamp.isoformat(),
        "timestamp_dt": timestamp,  # Keep datetime object for InfluxDB
        "request_id": request_id,
        "method": method,
        "api": api,
        "status": status,
        "latency_ms": latency
    }
    return log_entry

def write_to_influxdb(client, log_data):
    """
    Writes log data to InfluxDB.
    """
    try:
        # Create a Point for InfluxDB
        point = Point("api_logs") \
            .tag("method", log_data["method"]) \
            .tag("api", log_data["api"]) \
            .tag("status_code", str(log_data["status"])) \
            .field("latency_ms", log_data["latency_ms"]) \
            .field("request_id", log_data["request_id"]) \
            .time(log_data["timestamp_dt"], WritePrecision.NS)
        
        # Write the point to InfluxDB
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        return True
    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")
        return False

if __name__ == "__main__":
    print("Log generator started... Press Ctrl+C to stop.")
    print(f"Connecting to InfluxDB at {INFLUXDB_URL}")
    
    # Initialize InfluxDB client
    influx_client = None
    try:
        influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        # Test connection
        influx_client.ping()
        print("✅ Successfully connected to InfluxDB!")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to InfluxDB: {e}")
        print("Continuing with file logging only...")
    
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
                # Remove timestamp_dt before JSON serialization
                json_data = {k: v for k, v in log_data.items() if k != "timestamp_dt"}
                json_log_line = json.dumps(json_data)
                json_f.write(json_log_line + "\n")

                # --- 3. Write to InfluxDB ---
                influx_success = False
                if influx_client:
                    influx_success = write_to_influxdb(influx_client, log_data)
                
                # Print to console with status indicators
                status_indicator = "📊" if influx_success else "📝"
                print(f"{status_indicator} {raw_log_line}")
                
                # Flush files
                raw_f.flush()
                json_f.flush()

                # Wait for a random interval before the next log
                time.sleep(random.uniform(0.5, 3.0))

    except KeyboardInterrupt:
        print("\nLog generator stopped.")
    finally:
        if influx_client:
            influx_client.close()