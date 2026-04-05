import network
import socket
from machine import UART
import camera
import time

ssid = "Malik1"
password = "12345678"

# Connect to Wi-Fi network
sta = network.WLAN(network.STA_IF)
sta.active(True)

# Add a small delay to ensure Wi-Fi module is ready
time.sleep(2)

sta.connect(ssid, password)

# Wait until connected to Wi-Fi
max_attempts = 20  # Maximum attempts to wait for connection
attempts = 0

while not sta.isconnected() and attempts < max_attempts:
    print("Connecting to Wi-Fi...")
    attempts += 1
    time.sleep(1)

if not sta.isconnected():
    raise RuntimeError("Failed to connect to Wi-Fi")

# Get the IP address assigned by the router
ip_address = sta.ifconfig()[0]
print("ESP32-Cam IP:", "http://" + str(ip_address) + "/snapshot")
print("ESP32-Cam IP:", sta.ifconfig())

# UART 1 configuration for ESP32-Cam's camera
uart = UART(1, baudrate=115200, tx=3, rx=1)  # Replace with your actual TX and RX pin numbers

# Initialize the camera (ensure you have the correct method for your camera library)
camera.init(0, format=camera.JPEG)  # Adjust the initialization parameters as per your library

def snapshot_handler(client):
    try:
        snapshot = camera.capture()
        if snapshot:
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: image/jpeg\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n\r\n".format(len(snapshot))
            )
            client.send(response)
            client.send(snapshot)
        else:
            client.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")
    except Exception as e:
        print("Error capturing image:", e)
        client.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")
    finally:
        client.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ip_address, 80))
server.listen(1)

print("Starting server...")

while True:
    client, addr = server.accept()
    print("Client connected from:", addr)
    request = client.recv(1024)
   
    if b"/snapshot" in request:
        snapshot_handler(client)
    else:
        client.send("HTTP/1.1 404 Not Found\r\n\r\n")
        client.close()

