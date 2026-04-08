import network
import urequests
import time
import dht
from machine import Pin

# WiFi
ssid = "WachtwoordIsOverbodig"
password = "ScanGewoonQR420!"

# API
url = "http://192.168.178.149:5000/api/data"
api_key = "DitIsEchtEenGoedeAPIKey"

# WiFi verbinden
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    time.sleep(1)

print("Connected to WiFi")

# DHT sensor
sensor = dht.DHT11(Pin(4))

while True:
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        data = {
            "api_key": api_key,
            "temperature": temp,
            "humidity": hum
        }

        response = urequests.post(url, json=data)
        print(response.text)
        response.close()

    except Exception as e:
        print("Error:", e)

    time.sleep(60)