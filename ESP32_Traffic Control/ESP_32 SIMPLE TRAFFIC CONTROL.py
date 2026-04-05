import time
from machine import Pin

# Define LED pins
led_red = Pin(23, Pin.OUT)    # Red LED
led_yellow = Pin(22, Pin.OUT) # Yellow LED
led_green = Pin(21, Pin.OUT)  # Green LED

# Function to turn off a specific LED
def turn_off_led(led):
    led.value(0)  # Turn off the LED

# Function to blink a specific LED
def blink_led(led, duration):
    led.value(1)  # Turn on the LED
    start_time = time.ticks_ms()  # Get the current time in milliseconds
    
    while time.ticks_diff(time.ticks_ms(), start_time) < duration * 1000:
        # Check for commands while waiting
        command = input("Enter 0 to turn off the lights: ")
        if command == '0':
            turn_off_led(led_red)
            turn_off_led(led_yellow)
            turn_off_led(led_green)
            return
    
    turn_off_led(led)  # Turn off the LED after the specified duration

# Command-based control of LEDs
while True:
    command = input("Enter command (1 for Red, 2 for Green, 3 for Yellow): ")

    if command == '1':
        blink_led(led_red, 60)  # 1 minutes
    elif command == '2':
        blink_led(led_green, 60)  # 1 minutes
    elif command == '3':
        blink_led(led_yellow, 30)  # 1 minutes
    else:
        print("Invalid command. Please enter 1, 2, or 3.")

