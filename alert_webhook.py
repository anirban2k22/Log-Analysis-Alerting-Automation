#!/usr/bin/env python3
"""
Simple webhook server to receive and display Grafana alerts.
This demonstrates how to integrate external alerting systems.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import datetime
import threading
import time

class AlertHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle incoming webhook alerts from Grafana"""
        if self.path == '/alerts':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                alert_data = json.loads(post_data.decode('utf-8'))
                self.process_alert(alert_data)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "received"}')
                
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                print(f"Error processing alert: {e}")
        else:
            self.send_response(404)
            self.end_headers()
    
    def process_alert(self, alert_data):
        """Process and display the alert"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "="*60)
        print(f"🚨 ALERT RECEIVED at {timestamp}")
        print("="*60)
        
        # Extract key information
        if 'alerts' in alert_data:
            for alert in alert_data['alerts']:
                status = alert.get('status', 'unknown')
                title = alert.get('labels', {}).get('alertname', 'Unknown Alert')
                severity = alert.get('labels', {}).get('severity', 'unknown')
                description = alert.get('annotations', {}).get('description', '')
                
                # Color coding for severity
                severity_emoji = {
                    'critical': '🔴',
                    'warning': '🟡', 
                    'info': '🔵'
                }.get(severity, '⚪')
                
                print(f"{severity_emoji} {status.upper()}: {title}")
                print(f"   Severity: {severity}")
                if description:
                    print(f"   Description: {description}")
                
                # Show values if available
                if 'valueString' in alert:
                    print(f"   Value: {alert['valueString']}")
        
        print("="*60)
        
        # Log to file for persistence
        with open('logs/alerts.log', 'a') as f:
            f.write(f"[{timestamp}] {json.dumps(alert_data)}\n")
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass

def start_webhook_server():
    """Start the webhook server in a separate thread"""
    server = HTTPServer(('localhost', 8080), AlertHandler)
    print("🎯 Alert webhook server started on http://localhost:8080")
    print("   Ready to receive Grafana alerts at /alerts endpoint")
    server.serve_forever()

if __name__ == "__main__":
    import os
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    print("Starting Alert Webhook Server...")
    print("This will receive and display alerts from Grafana")
    print("Press Ctrl+C to stop")
    
    try:
        start_webhook_server()
    except KeyboardInterrupt:
        print("\nAlert webhook server stopped.")
