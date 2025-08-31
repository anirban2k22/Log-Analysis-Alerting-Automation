#!/usr/bin/env python3
"""
Advanced traffic simulator for testing monitoring and alerting systems.
Simulates various scenarios like traffic spikes, outages, and slow responses.
"""

import random
import datetime
import uuid
import time
import os
import json
import threading
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuration
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
API_ENDPOINTS = ["/login", "/api/v1/users", "/api/v1/products", "/logout", "/health"]
STATUS_CODES = [200, 201, 202, 400, 401, 403, 404, 500, 503]

# InfluxDB Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "my-super-secret-token"
INFLUXDB_ORG = "my-org"
INFLUXDB_BUCKET = "my-bucket"

# Simulation modes
class TrafficPattern:
    NORMAL = "normal"
    SPIKE = "spike"
    OUTAGE = "outage"
    SLOW_RESPONSE = "slow_response"
    HIGH_ERROR_RATE = "high_error_rate"

class TrafficSimulator:
    def __init__(self):
        self.influx_client = None
        self.current_pattern = TrafficPattern.NORMAL
        self.pattern_start_time = time.time()
        self.pattern_duration = 0
        self.base_request_rate = 1.0  # requests per second
        
        # Initialize InfluxDB connection
        try:
            self.influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
            self.influx_client.ping()
            print("✅ Connected to InfluxDB")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to InfluxDB: {e}")
    
    def generate_log_entry(self):
        """Generate a log entry based on current traffic pattern"""
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        request_id = str(uuid.uuid4())
        method = random.choice(HTTP_METHODS)
        api = random.choice(API_ENDPOINTS)
        
        # Adjust based on current pattern
        status, latency = self._get_pattern_specific_values()
        
        return {
            "timestamp": timestamp.isoformat(),
            "timestamp_dt": timestamp,
            "request_id": request_id,
            "method": method,
            "api": api,
            "status": status,
            "latency_ms": latency
        }
    
    def _get_pattern_specific_values(self):
        """Get status and latency based on current traffic pattern"""
        if self.current_pattern == TrafficPattern.NORMAL:
            status = random.choices(STATUS_CODES, weights=[30, 10, 10, 5, 3, 2, 2, 3, 1])[0]
            latency = random.randint(50, 500)
            
        elif self.current_pattern == TrafficPattern.SPIKE:
            # More traffic, slightly higher latency
            status = random.choices(STATUS_CODES, weights=[25, 8, 8, 8, 5, 3, 3, 5, 2])[0]
            latency = random.randint(100, 800)
            
        elif self.current_pattern == TrafficPattern.OUTAGE:
            # High error rates, service unavailable
            status = random.choices([500, 503, 504], weights=[1, 2, 1])[0]
            latency = random.randint(5000, 10000)  # Very slow
            
        elif self.current_pattern == TrafficPattern.SLOW_RESPONSE:
            # Normal status codes but high latency
            status = random.choices(STATUS_CODES, weights=[30, 10, 10, 5, 3, 2, 2, 3, 1])[0]
            latency = random.randint(1500, 3000)
            
        elif self.current_pattern == TrafficPattern.HIGH_ERROR_RATE:
            # High proportion of 4xx and 5xx errors
            status = random.choices(STATUS_CODES, weights=[10, 3, 3, 15, 10, 8, 8, 15, 10])[0]
            latency = random.randint(50, 500)
        
        return status, latency
    
    def _get_request_interval(self):
        """Get request interval based on current pattern"""
        base_interval = 1.0 / self.base_request_rate
        
        if self.current_pattern == TrafficPattern.SPIKE:
            return base_interval * 0.2  # 5x more requests
        elif self.current_pattern == TrafficPattern.OUTAGE:
            return base_interval * 2.0   # Slower during outage
        else:
            return base_interval + random.uniform(-0.3, 0.3)
    
    def change_pattern(self, pattern, duration=60):
        """Change traffic pattern for a specified duration"""
        self.current_pattern = pattern
        self.pattern_start_time = time.time()
        self.pattern_duration = duration
        
        pattern_emoji = {
            TrafficPattern.NORMAL: "🟢",
            TrafficPattern.SPIKE: "🔥",
            TrafficPattern.OUTAGE: "🔴",
            TrafficPattern.SLOW_RESPONSE: "🐌",
            TrafficPattern.HIGH_ERROR_RATE: "⚠️"
        }
        
        emoji = pattern_emoji.get(pattern, "⚪")
        print(f"\n{emoji} Switching to {pattern.upper()} pattern for {duration} seconds")
    
    def update_pattern(self):
        """Update pattern based on time and randomness"""
        current_time = time.time()
        
        # Check if current pattern should expire
        if (self.pattern_duration > 0 and 
            current_time - self.pattern_start_time > self.pattern_duration):
            self.change_pattern(TrafficPattern.NORMAL, 0)
        
        # Randomly introduce incidents (5% chance every 30 seconds)
        if (self.current_pattern == TrafficPattern.NORMAL and 
            random.random() < 0.05 and 
            current_time - self.pattern_start_time > 30):
            
            incident_patterns = [
                (TrafficPattern.SPIKE, 30),
                (TrafficPattern.OUTAGE, 20),
                (TrafficPattern.SLOW_RESPONSE, 40),
                (TrafficPattern.HIGH_ERROR_RATE, 35)
            ]
            
            pattern, duration = random.choice(incident_patterns)
            self.change_pattern(pattern, duration)
    
    def write_to_influxdb(self, log_data):
        """Write log data to InfluxDB"""
        if not self.influx_client:
            return False
        
        try:
            point = Point("api_logs") \
                .tag("method", log_data["method"]) \
                .tag("api", log_data["api"]) \
                .tag("status_code", str(log_data["status"])) \
                .tag("traffic_pattern", self.current_pattern) \
                .field("latency_ms", log_data["latency_ms"]) \
                .field("request_id", log_data["request_id"]) \
                .time(log_data["timestamp_dt"], WritePrecision.NS)
            
            write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
            return True
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
            return False
    
    def run(self):
        """Main simulation loop"""
        print("🎭 Advanced Traffic Simulator Started")
        print("   - Simulates various traffic patterns and incidents")
        print("   - Press Ctrl+C to stop")
        
        try:
            while True:
                # Update traffic pattern
                self.update_pattern()
                
                # Generate and send log entry
                log_data = self.generate_log_entry()
                influx_success = self.write_to_influxdb(log_data)
                
                # Display log with pattern indicator
                pattern_indicators = {
                    TrafficPattern.NORMAL: "📊",
                    TrafficPattern.SPIKE: "🔥", 
                    TrafficPattern.OUTAGE: "💥",
                    TrafficPattern.SLOW_RESPONSE: "🐌",
                    TrafficPattern.HIGH_ERROR_RATE: "⚠️"
                }
                
                indicator = pattern_indicators.get(self.current_pattern, "📊")
                status_indicator = "✅" if influx_success else "❌"
                
                print(f"{indicator}{status_indicator} [{log_data['timestamp']}] "
                      f"method={log_data['method']} api={log_data['api']} "
                      f"status={log_data['status']} latency={log_data['latency_ms']}ms "
                      f"pattern={self.current_pattern}")
                
                # Wait for next request
                time.sleep(self._get_request_interval())
                
        except KeyboardInterrupt:
            print("\n🛑 Traffic simulator stopped")
        finally:
            if self.influx_client:
                self.influx_client.close()

if __name__ == "__main__":
    simulator = TrafficSimulator()
    simulator.run()
