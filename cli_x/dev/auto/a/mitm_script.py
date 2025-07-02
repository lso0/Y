from mitmproxy import ctx
import json
from datetime import datetime
import os

class RequestLogger:
    def __init__(self):
        self.log_file = "requests.log"
        ctx.log.info("RequestLogger initialized")
        
    def request(self, flow):
        # Log request details
        with open(self.log_file, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            request_data = {
                "timestamp": timestamp,
                "type": "request",
                "method": flow.request.method,
                "url": flow.request.url,
                "headers": dict(flow.request.headers),
                "content": flow.request.content.decode('utf-8', errors='ignore') if flow.request.content else None
            }
            f.write(json.dumps(request_data) + "\n")
            ctx.log.info(f"Request: {flow.request.method} {flow.request.url}")
            
    def response(self, flow):
        # Log response details
        with open(self.log_file, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            response_data = {
                "timestamp": timestamp,
                "type": "response",
                "status_code": flow.response.status_code,
                "headers": dict(flow.response.headers),
                "content": flow.response.content.decode('utf-8', errors='ignore') if flow.response.content else None
            }
            f.write(json.dumps(response_data) + "\n")
            ctx.log.info(f"Response: {flow.response.status_code} for {flow.request.url}")

    def error(self, flow):
        ctx.log.error(f"Error in flow: {flow.error}")

addons = [
    RequestLogger()
] 