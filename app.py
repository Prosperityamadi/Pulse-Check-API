from flask import Flask, request, jsonify
from threading import Timer, Lock
from datetime import datetime
import json

app = Flask(__name__)

# Monitor data schema:
# {
#     "device-123": {
#         "id": "device-123",
#         "timeout": 60,
#         "alert_email": "admin@critmon.com",
#         "status": "active" | "down" | "paused",
#         "timer": Timer object,
#         "last_heartbeat": timestamp
#     }
# }
monitors = {}
monitors_lock = Lock()


@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Pulse Check API",
        "status": "running"
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Pulse-Check API",
        "timestamp": datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    print("Pulse-Check API Starting...")
    print("Listening on http://localhost:5000")
    print("Press CTRL+C to stop")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)

