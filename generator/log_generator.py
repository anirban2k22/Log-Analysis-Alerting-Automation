import random
import datetime
import uuid

# --- Configuration for log generation ---
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
API_ENDPOINTS = ["/login", "/api/v1/users", "/api/v1/products", "/logout", "/health"]
STATUS_CODES = [200, 201, 202, 400, 401, 403, 404, 500, 503]

def generate_log_line():
    """
    Generates a single, randomized log line in the specified format.
    """
    timestamp = datetime.datetime.now().isoformat()
    request_id = uuid.uuid4().hex[:8]
    method = random.choice(HTTP_METHODS)
    api = random.choice(API_ENDPOINTS)
    status = random.choice(STATUS_CODES)
    latency = random.randint(10, 2000)  # Latency in milliseconds

    log_line = (
        f"[{timestamp}] request_id={request_id} method={method} "
        f"api={api} status={status} latency={latency}ms"
    )
    return log_line

if __name__ == "__main__":
    # For Day 1, we just generate and print 10 sample log lines to the console.
    print("--- Generating 10 sample log lines ---")
    for _ in range(10):
        log = generate_log_line()
        print(log)