import network
import socket
import select
from machine import Pin, Timer
import camera
import time

LED_FLASH_PIN = 4  # GPIO pin for the built-in LED flash
LED_STATUS_PIN = 33  # GPIO pin for the built-in status LED
BUTTON_PIN = 12  # GPIO pin for the push button

status_led = None
button = None
debug_log = []

def log_debug(message):
    global debug_log
    debug_log.append(message)
    print(message)
    with open('/debug_log.txt', 'a') as f:
        f.write(message + '\n')

def blink_led(timer):
    global status_led
    if status_led:
        status_led.value(not status_led.value())  # Toggle the LED state

def connect_to_wifi(ssid, password, max_attempts=20):
    global status_led
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.disconnect()  # Ensure the module is in a clean state
    time.sleep(1)  # Give time for the disconnect to complete
    attempts = 0

    status_led = initialize_led(LED_STATUS_PIN)
    timer = Timer(0)
    timer.init(period=500, mode=Timer.PERIODIC, callback=blink_led)

    while not sta.isconnected() and attempts < max_attempts:
        log_debug("Connecting to Wi-Fi...")
        try:
            sta.connect(ssid, password)
        except Exception as e:
            log_debug(f"Wi-Fi connection error: {e}")
            break
        attempts += 1
        time.sleep(1)
        log_debug(f"Attempt: {attempts}")
        if sta.isconnected():
            log_debug("Wi-Fi connected")
            break
    timer.deinit()  # Stop blinking
    if status_led:
        status_led.on()  # Turn the status LED on

    if not sta.isconnected():
        raise RuntimeError("Failed to connect to Wi-Fi")

    log_debug(f"Connected to Wi-Fi: {ssid}")
    time.sleep(1)  # Ensure the print statement completes
    ip_address = sta.ifconfig()[0]
    snapshotAPI = "http://" + str(ip_address) + "/snapshot"
    log_debug(f"ESP32-Cam Snapshot API: {snapshotAPI}")
    time.sleep(1)  # Ensure the print statement completes
    log_debug(f"ESP32-Cam Stream API: http://{ip_address}/stream")
    time.sleep(1)  # Ensure the print statement completes

    return ip_address

def initialize_camera():
    try:
        camera.deinit()  # Ensure camera is deinitialized first
        time.sleep(2)  # Short delay before initializing the camera
        camera.init(0, format=camera.JPEG)
        camera.framesize(camera.FRAME_QVGA)  # Set resolution to QVGA (320x240)
        camera.quality(10)  # Set JPEG quality (lower value means higher compression)
        camera.speffect(camera.EFFECT_BW)  # Set effect to black and white
        log_debug("Camera initialized")
    except Exception as e:
        log_debug(f"Error initializing camera: {e}")
        raise

def initialize_led(pin):
    led = Pin(pin, Pin.OUT)
    led.off()  # Ensure the LED is off initially
    return led

def initialize_button(pin):
    button = Pin(pin, Pin.IN, Pin.PULL_UP)  # Initialize the button with an internal pull-up resistor
    return button

def handle_snapshot_request(client_socket, flash_led):
    try:
        flash_led.on()  # Turn on the LED flash
        time.sleep(0.1)  # Small delay to allow LED flash to light up
        snapshot = camera.capture()
        flash_led.off()  # Turn off the LED flash
        if snapshot:
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: image/jpeg\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n\r\n".format(len(snapshot))
            )
            client_socket.send(response.encode())
            client_socket.send(snapshot)
        else:
            client_socket.send("HTTP/1.1 500 Internal Server Error\r\n\r\n".encode())
    except Exception as e:
        log_debug(f"Error capturing image: {e}")
        client_socket.send("HTTP/1.1 500 Internal Server Error\r\n\r\n".encode())
    finally:
        client_socket.close()

def handle_stream_request(client_socket):
    try:
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
            "Connection: keep-alive\r\n\r\n"
        )
        client_socket.send(response.encode())
        while True:
            snapshot = camera.capture()
            if snapshot:
                frame_header = (
                    "--frame\r\n"
                    "Content-Type: image/jpeg\r\n"
                    "Content-Length: {}\r\n\r\n".format(len(snapshot))
                )
                client_socket.send(frame_header.encode())
                client_socket.send(snapshot)
                client_socket.send("\r\n".encode())
                time.sleep(0.05)  # Adjust the delay as needed for frame rate
            else:
                client_socket.send("HTTP/1.1 500 Internal Server Error\r\n\r\n".encode())
                break
    except Exception as e:
        log_debug(f"Error streaming video: {e}")
        client_socket.send("HTTP/1.1 500 Internal Server Error\r\n\r\n".encode())
    finally:
        client_socket.close()

def handle_debug_request(client_socket):
    try:
        # Serve the debug log file if it exists
        with open('/debug_log.txt', 'r') as f:
            log_content = f.read()
        
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n\r\n".format(len(log_content))
        )
        client_socket.send(response.encode())
        client_socket.send(log_content.encode())
    except Exception as e:
        log_debug(f"Error serving debug log: {e}")
        client_socket.send("HTTP/1.1 500 Internal Server Error\r\n\r\n".encode())
    finally:
        client_socket.close()

def start_server(ip_address, port=80):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ip_address, port))
    server_socket.listen(5)  # Queue up to 5 connections
    log_debug(f"Server started at {ip_address}:{port}")
    time.sleep(1)  # Ensure the print statement completes
    return server_socket

def main():
    time.sleep(10)  # Increase the delay to ensure proper initialization

    # Wait for button press before starting
    button = initialize_button(BUTTON_PIN)
    log_debug("Waiting for button press to start...")
    while button.value() == 1:
        time.sleep(0.1)

    ssid = "VisualInteract2"
    password = "12345679"
    ip_address = connect_to_wifi(ssid, password)
    initialize_camera()
    flash_led = initialize_led(LED_FLASH_PIN)

    server_socket = start_server(ip_address)
    inputs = [server_socket]
    while True:
        readable, _, _ = select.select(inputs, [], [])
        for s in readable:
            if s is server_socket:
                client_socket, addr = server_socket.accept()
                log_debug(f"Client connected from: {addr}")
                inputs.append(client_socket)
            else:
                try:
                    request = s.recv(1024)
                    if not request:
                        inputs.remove(s)
                        s.close()
                    elif b"/snapshot" in request:
                        handle_snapshot_request(s, flash_led)
                    elif b"/stream" in request:
                        handle_stream_request(s)
                    elif b"/debug" in request:
                        handle_debug_request(s)
                    else:
                        s.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())
                        s.close()
                except Exception as e:
                    log_debug(f"Client handler error: {e}")
                    inputs.remove(s)
                    s.close()

main()

