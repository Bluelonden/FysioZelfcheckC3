from flask import Flask, request, jsonify
import ssl
import sqlite3
import time

app = Flask(__name__)
API_KEY = "DitIsEchtEenGoedeAPIKey"

@app.route('/test')
def test():
    return "Server werkt"

@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()

    if not data or data.get("api_key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    temperature = data.get("temperature")
    humidity = data.get("humidity")

    if temperature is None or humidity is None:
        return jsonify({"error": "Missing data"}), 400

    conn = sqlite3.connect("dht11.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO metingen (timestamp, temperature, humidity) VALUES (?, ?, ?)",
        (timestamp, temperature, humidity)
    )
    conn.commit()
    conn.close()

    print("Data ontvangen:", temperature, humidity)

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
   # ,host='0.0.0.0', port=5000)