import lgpio
import time
import sys
import select
import termios
import tty

# --- CONFIGURATION ---
# Raspberry Pi 5 usually uses Chip 4. 
CHIP_ID = 4  
THROTTLE_PIN = 12       # BCM 24 = Physical Pin 18
STEERING_PIN = 13
PWM_FREQ = 50       # 50 Hz is standard for servos

# --- MATH: Calculating Duty Cycle % ---
# Period at 50Hz = 20ms (0.02s)
# 0 degrees   = ~0.5ms pulse -> 2.5% Duty Cycle
# 90 degrees  = ~1.5ms pulse -> 7.5% Duty Cycle
# 180 degrees = ~2.5ms pulse -> 12.5% Duty Cycle

# ^^^ NOTE Above was greg's values but that may not be correct
# What I think the correct values are is
# 0 degrees = 1ms pulse -> 5% Duty Cycle
# 90 degres = 1.5ms pulse -> 7.5% Duty Cycle
# 180 degrees = 2ms pulse -> 10% Duty cycle
# NOTE the DutyCycle% value is what goes nto the tx_pwm method

PRESET1=5.0
PRESET2=7.5
PRESET3=10.0
PRESET4=8.0
PRESET5=7.0
makeDefaultFaster=True
if makeDefaultFaster:
    PRESET4+=.55
    PRESET5-=.5

#lgpio.tx_pwm(h, GPIO_PIN, PWM_FREQ, PRESET2) #DRIVE motor
#lgpio.tx_pwm(h, GPIO_PIN2, PWM_FREQ, PRESET2) #TURN motor


# Save the terminal settings so we can restore them later
settings = termios.tcgetattr(sys.stdin)
h=None

def get_key():
    """Reads a single keypress from the terminal."""
    tty.setraw(sys.stdin.fileno())
    # This waits for a key with a 0.1s timeout
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


# --- Placeholder for your PWM logic ---
def move_forward():
    print("Moving Forward ↑")
    lgpio.tx_pwm(h, THROTTLE_PIN, PWM_FREQ, PRESET4)

def move_backward():
    print("Moving Backward ↓")
    lgpio.tx_pwm(h, THROTTLE_PIN, PWM_FREQ, PRESET5)

def move_forward_FAST():
    print("Moving Forward ↑")
    lgpio.tx_pwm(h, THROTTLE_PIN, PWM_FREQ, PRESET3)

def move_backward_FAST():
    print("Moving Backward ↓")
    lgpio.tx_pwm(h, THROTTLE_PIN, PWM_FREQ, PRESET1)

def turn_left():
    print("Turning Left ←")
    lgpio.tx_pwm(h, STEERING_PIN, PWM_FREQ, PRESET3)

def turn_right():
    print("Turning Right →")
    lgpio.tx_pwm(h, STEERING_PIN, PWM_FREQ, PRESET1)

def turn_neutral():
    print("Turning Neutral .")
    lgpio.tx_pwm(h, STEERING_PIN, PWM_FREQ, PRESET2)

def stop_rover():
    print("STOP - Neutral ■")
    lgpio.tx_pwm(h, THROTTLE_PIN, PWM_FREQ, PRESET2)
    lgpio.tx_pwm(h, STEERING_PIN, PWM_FREQ, PRESET2)


def main():
    global h
    try:
        # 1. Open the GPIO Chip
        print(f"Opening GPIO Chip {CHIP_ID}...")
        h = lgpio.gpiochip_open(CHIP_ID)
        lgpio.gpio_claim_output(h, THROTTLE_PIN)
        lgpio.gpio_claim_output(h, STEERING_PIN)
        
        
	    # Collect events until released
        
        print("""
        ---------------------------
        Reading from Terminal...
        Use WASD to move.
        Spacebar or 'k' to stop.
        Press 'Ctrl+C' to quit.
        ---------------------------
        """)
        while True:
            key = get_key()
            
            if key == 'w':
                move_forward()
            elif key == 's':
                move_backward()
            elif key == 'W':
                move_forward_FAST()
            elif key == 'S':
                move_backward_FAST()
            elif key == 'a':
                turn_left()
            elif key == 'd':
                turn_right()
            elif key == 'r':
                turn_neutral()
            elif key == ' ' or key == 'k':
                stop_rover()
            elif key == '\x03': # Ctrl+C
                break
	       

    except lgpio.error as e:
        print(f"LGPIO Error: {e}")
        print("If 'chip not found', change CHIP_ID to 0.")
        
    except KeyboardInterrupt: 
        print("\nStopping...")

    finally:
        if h is not None:
            # Stop PWM by setting duty cycle to 0 or frequency to 0 GPIO numbers (BCM) and Physical Pin numb    	   lgpio.tx_pwm(h, GPIO_PIN, 0, 0)
           lgpio.gpiochip_close(h)
           termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
           print("GPIO Closed.")

if __name__ == "__main__":
    main()
