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

def start_timer(monitor_id, timeout_seconds):
    """Start or reset the countdown timer for a monitor."""
    with monitors_lock:
        if monitor_id in monitors:
            if monitors[monitor_id]['timer'] is not None:
                monitors[monitor_id]['timer'].cancel()

            new_timer = Timer(timeout_seconds, trigger_alert,
                              args=[monitor_id])
            new_timer.start()

            monitors[monitor_id]['timer'] = new_timer
            monitors[monitor_id]['status'] = 'active'
            monitors[monitor_id]['last_heartbeat'] = datetime.now().isoformat()

def cancel_timer(monitor_id):
    """Stop a timer without triggering an alert. Caller must hold monitors_lock."""
    if monitor_id in monitors and monitors[monitor_id]['timer'] is not None:
        monitors[monitor_id]['timer'].cancel()
        monitors[monitor_id]['timer'] = None

@app.route('/', methods=['GET'])
def index():
    """Root endpoint listing all available API routes."""
    return jsonify({
        "message": "Welcome to Pulse-Check API",
        "endpoints": [
            "POST /monitors",
            "GET /monitors",
            "GET /monitors/<id>",
            "DELETE /monitors/<id>",
            "POST /monitors/<id>/heartbeat",
            "POST /monitors/<id>/pause",
            "GET /health"
        ]
    }), 200

@app.route('/monitors', methods=['POST'])
def create_monitor():
    """Register a new device for monitoring.

    Request body:
    {
        "id": "device-123",
        "timeout": 60,
        "alert_email": "admin@critmon.com"
    }
    """
    data = request.get_json()

    if not data or 'id' not in data or 'timeout' not in data:
        return jsonify({
            "error": "Missing required fields: 'id' and 'timeout'"
        }), 400

    monitor_id = data['id']
    timeout = data['timeout']
    alert_email = data.get('alert_email', 'not_provided@example.com')

    if monitor_id in monitors:
        return jsonify({
            "error": f"Monitor {monitor_id} already exists"
        }), 409

    with monitors_lock:
        monitors[monitor_id] = {
            'id': monitor_id,
            'timeout': timeout,
            'alert_email': alert_email,
            'status': 'active',
            'timer': None,
            'last_heartbeat': None,
            'created_at': datetime.now().isoformat()
        }

    start_timer(monitor_id, timeout)

    return jsonify({
        "message": f"Monitor {monitor_id} created successfully",
        "monitor": {
            "id": monitor_id,
            "timeout": timeout,
            "status": "active"
        }
    }), 201

@app.route('/monitors/<monitor_id>/heartbeat', methods=['POST'])
def heartbeat(monitor_id):
    """Device sends a heartbeat to reset its countdown timer.

    Also revives a 'down' monitor or resumes a 'paused' one.
    """
    with monitors_lock:
        if monitor_id not in monitors:
            return jsonify({
                "error": f"Monitor {monitor_id} not found"
            }), 404

        monitor = monitors[monitor_id]

        if monitor['status'] in ('down', 'paused'):
            monitor['status'] = 'active'

    start_timer(monitor_id, monitors[monitor_id]['timeout'])

    return jsonify({
        "message": f"Heartbeat received for {monitor_id}",
        "status": "timer_reset",
        "next_expiry": monitors[monitor_id]['timeout']
    }), 200

@app.route('/monitors/<monitor_id>/pause', methods=['POST'])
def pause_monitor(monitor_id):
    """Pause monitoring for a device (e.g., during planned maintenance)."""
    with monitors_lock:
        if monitor_id not in monitors:
            return jsonify({
                "error": f"Monitor {monitor_id} not found"
            }), 404

        cancel_timer(monitor_id)
        monitors[monitor_id]['status'] = 'paused'

    return jsonify({
        "message": f"Monitor {monitor_id} paused",
        "status": "paused"
    }), 200

@app.route('/monitors', methods=['GET'])
def list_monitors():
    """Get all monitors with their current status."""
    with monitors_lock:
        monitor_list = []
        for monitor_id, monitor in monitors.items():
            monitor_list.append({
                'id': monitor['id'],
                'timeout': monitor['timeout'],
                'status': monitor['status'],
                'alert_email': monitor['alert_email'],
                'last_heartbeat': monitor['last_heartbeat'],
                'created_at': monitor.get('created_at')
            })

    return jsonify({
        "monitors": monitor_list,
        "total": len(monitor_list)
    }), 200

@app.route('/monitors/<monitor_id>', methods=['GET'])
def get_monitor(monitor_id):
    """Get detailed status of a specific monitor."""
    with monitors_lock:
        if monitor_id not in monitors:
            return jsonify({
                "error": f"Monitor {monitor_id} not found"
            }), 404

        monitor = monitors[monitor_id]
        return jsonify({
            'id': monitor['id'],
            'timeout': monitor['timeout'],
            'status': monitor['status'],
            'alert_email': monitor['alert_email'],
            'last_heartbeat': monitor['last_heartbeat'],
            'created_at': monitor.get('created_at')
        }), 200

@app.route('/monitors/<monitor_id>', methods=['DELETE'])
def delete_monitor(monitor_id):
    """Remove a monitor and cancel its timer."""
    with monitors_lock:
        if monitor_id not in monitors:
            return jsonify({
                "error": f"Monitor {monitor_id} not found"
            }), 404

        cancel_timer(monitor_id)
        del monitors[monitor_id]

    return jsonify({
        "message": f"Monitor {monitor_id} deleted successfully"
    }), 200

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

