import network
import urequests as requests
from machine import Pin
import time

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('VisualInteract1', '12345678')

while not wlan.isconnected():
    print("Connecting to Wi-Fi...")
    time.sleep(1)

print("Wi-Fi connected")

# Flask server IP and port
FLASK_IP = '192.168.137.119'
FLASK_PORT = 5000
road1 = 0
road2 = 0
road3 = 0
road4 = 0

# Define LED pins for Road 1
led_red_road1 = Pin(33, Pin.OUT)
led_yellow_road1 = Pin(25, Pin.OUT)
led_green_road1 = Pin(26, Pin.OUT)

# Define LED pins for Road 2
led_red_road2 = Pin(23, Pin.OUT) # ?
led_yellow_road2 = Pin(22, Pin.OUT)
led_green_road2 = Pin(21, Pin.OUT)

# Define LED pins for Road 3
led_red_road3 = Pin(27, Pin.OUT)
led_yellow_road3 = Pin(14, Pin.OUT)
led_green_road3 = Pin(13, Pin.OUT)

# Define LED pins for Road 4
led_red_road4 = Pin(19, Pin.OUT)
led_yellow_road4 = Pin(18, Pin.OUT)
led_green_road4 = Pin(5, Pin.OUT)

def blink(led):
    led.on()
    time.sleep(0.25)
    led.off()
    time.sleep(0.25)
    led.on()
    time.sleep(0.25)
    led.off()
    time.sleep(0.25)
    led.on()
    time.sleep(0.25)
    led.off()

# Function to control traffic lights for each road
def control_traffic_lights(green_road, green_on_time):
    # Turn off all lights initially
    led_red_road1.on()
    led_yellow_road1.off()
    led_green_road1.off()
    led_red_road2.on()
    led_yellow_road2.off()
    led_green_road2.off()
    led_red_road3.on()
    led_yellow_road3.off()
    led_green_road3.off()
    led_red_road4.on()
    led_yellow_road4.off()
    led_green_road4.off()
    # Determine which road's light is green and change other lights accordingly
    if green_road == 1:
        led_red_road1.off()
#         led_yellow_road1.on()
#         time.sleep(1)
#         led_yellow_road1.off()
        blink(led_yellow_road1)
        led_green_road1.on()
        time.sleep(green_on_time)
    elif green_road == 2:
        led_red_road2.off()
#         led_yellow_road2.on()
#         time.sleep(1)
#         led_yellow_road2.off()
        blink(led_yellow_road2)
        led_green_road2.on()
        time.sleep(green_on_time)
    elif green_road == 3:
        led_red_road3.off()
#         led_yellow_road3.on()
#         time.sleep(1)
#         led_yellow_road3.off()
        blink(led_yellow_road3)
        led_green_road3.on()
        time.sleep(green_on_time)
    elif green_road == 4:
        led_red_road4.off()
#         led_yellow_road4.on()
#         time.sleep(1)
#         led_yellow_road4.off()
        blink(led_yellow_road4)
        led_green_road4.on()
        time.sleep(green_on_time)

# green_time = 10
while True:
    try:
        # Request data from Flask server
        response = requests.post('http://{}:{}/set_traffic_lights'.format(FLASK_IP, FLASK_PORT), json={'road1': road1, 'road2': road2, 'road3': road3, 'road4': road4 })
        data = response.json()
        print("Data received from server:", data)
        response.close()

        # Change signals based on received data
        control_traffic_lights(1, data['road1'])
        control_traffic_lights(2, data['road2'])
        control_traffic_lights(3, data['road3'])
        control_traffic_lights(4, data['road4'])
        
    except Exception as e:
        print("Error:", e)
        time.sleep(1) # Wait for 1 second before retrying

