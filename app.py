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

def trigger_alert(monitor_id):
    """Called when a timer expires, indicating the device missed its heartbeat."""
    with monitors_lock:
        if monitor_id in monitors:
            monitor = monitors[monitor_id]

            if monitor['status'] != 'down':
                alert_message = {
                    "ALERT": f"Device {monitor_id} is down!",
                    "time": datetime.now().isoformat(),
                    "device_id": monitor_id,
                    "alert_email": monitor.get('alert_email', 'N/A')
                }

                print("=" * 60)
                print(json.dumps(alert_message, indent=2))
                print("=" * 60)

                monitor['status'] = 'down'
                monitor['timer'] = None


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

