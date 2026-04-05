import network
from machine import UART
import camera
import socket

ssid = "Malik "
password = "12345678"

# Connect to Wi-Fi network
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(ssid, password)

# Wait until connected to Wi-Fi
while not sta.isconnected():
    pass

# Get the IP address assigned by the router
ip_address = sta.ifconfig()[0]
print("ESP32-Cam IP:", "http://"+str(ip_address)+"/snapshot")
print("ESP32-Cam IP:", sta.ifconfig())


# UART 1 configuration for ESP32-Cam's camera
uart = UART(1, baudrate=115200, tx=3, rx=1)  # Replace with your actual TX and RX pin numbers
camera.init(uart)

def snapshot_handler(client):
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: image/jpeg\r\n\r\n"
    )
    client.send(response)
    snapshot = camera.capture()
    print(snapshot)
    client.send(snapshot)
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
   
    client.close()

