import network
from machine import UART
import camera
import socket
import time

ssid = "Malik"
password = "12345678"

# Connect to Wi-Fi network
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(ssid, password)

# Wait until connected to Wi-Fi
while not sta.isconnected():
    time.sleep(1)

# Get the IP address assigned by the router
ip_address = sta.ifconfig()[0]
print("ESP32-Cam IP:", "http://" + str(ip_address) + "/stream")
print("ESP32-Cam IP:", sta.ifconfig())

# UART 1 configuration for ESP32-Cam's camera
uart = UART(1, baudrate=115200, tx=3, rx=1)  # Replace with your actual TX and RX pin numbers
camera.init(uart)

def stream_handler(client):
    boundary = "frame"
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: multipart/x-mixed-replace; boundary={}\r\n\r\n"
        "--{}\r\n".format(boundary, boundary)
    )
    client.send(response)
    
    try:
        while True:
            snapshot = camera.capture()
            frame_header = (
                "Content-Type: image/jpeg\r\n"
                "Content-Length: {}\r\n\r\n".format(len(snapshot))
            )
            client.send(frame_header)
            client.send(snapshot)
            client.send("\r\n--{}\r\n".format(boundary))
            
            # Add a small delay to manage frame rate
            time.sleep(0.1)
    except Exception as e:
        print("Stream ended:", e)
    finally:
        client.close()

# Create and configure the server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ip_address, 80))
server.listen(1)

print("Starting server...")

while True:
    client, addr = server.accept()
    print("Client connected from:", addr)
    request = client.recv(1024)
   
    if b"/stream" in request:
        stream_handler(client)
    else:
        # Send a 404 response for any other request
        client.send("HTTP/1.1 404 Not Found\r\n\r\n")
        client.close()

