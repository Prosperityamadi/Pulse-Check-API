from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Pulse Check API",
        "status": "running"
    })


@app.route("/api/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Pulse Check API"
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
