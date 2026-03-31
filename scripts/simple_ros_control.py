import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math
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
PRESET4=8.05
PRESET5=7.0
makeDefaultFaster=True
if makeDefaultFaster:
    PRESET4+=.4
    PRESET5-=.4

#lgpio.tx_pwm(h, THROTTLE_PIN, PWM_FREQ, PRESET2) #DRIVE motor
#lgpio.tx_pwm(h, STEERING_PIN, PWM_FREQ, PRESET2) #TURN motor

h=None


class AckermannBridge(Node):
    def __init__(self):
        super().__init__('ackermann_bridge')
        
        # Subscribe to the Nav2 velocity commands
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # --- ROVER HARDWARE PARAMETERS ---
        # Connor/Greg: Measure these on the physical rover!
        self.wheelbase = 0.405  # Distance between front and rear axles in meters
        self.max_steering_angle = math.radians(30.0)  # Max physical wheel turn
        
        self.get_logger().info("Ackermann Bridge Node Started. Waiting for /cmd_vel...")

    def cmd_vel_callback(self, msg):
        # 1. Extract desired velocities from Nav2
        v = msg.linear.x       # Desired forward speed (m/s)
        omega = -msg.angular.z  # Desired rotation rate (rad/s)
        
        # 2. Handle the "Zero Velocity" Trap
        # If the rover is stopped (or barely moving), we cannot divide by v.
        if abs(v) < 0.01:
            steering_angle_rad = 0.0
            throttle_target = 0.0
        else:
            # 3. The Ackermann Kinematics Math
            # delta = arctan((L * omega) / v)
            steering_angle_rad = math.atan((self.wheelbase * omega) / v)
            
            # Clip the angle to the physical limits of the steering rack
            steering_angle_rad = max(-self.max_steering_angle, min(self.max_steering_angle, steering_angle_rad))
            
            throttle_target = v

        # 4. Pass to the hardware translation layer
        self.send_to_hardware(throttle_target, steering_angle_rad)

    def map_range(self, x, in_min, in_max, out_min, out_max):
        """Standard Arduino-style map function for converting ranges"""
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def send_to_hardware(self, target_velocity, steering_angle_rad):
        """
        GREG'S HARDWARE ZONE:
        Convert the physical units into PWM values and send to GPIO.
        """
        # --- Example: Steering Servo (Standard 1ms-2ms PWM) ---
        # Assuming steering servo is centered at 90 degrees (1.5ms pulse)
        # Left = 60 deg, Right = 120 deg
        steering_degrees = math.degrees(steering_angle_rad)
        
        # Map physical angle (-30 to 30) to servo angle (60 to 120)
        # Adjust these bounds based on how the servo is physically mounted
        steering_pwm = self.map_range(steering_degrees, -30.0, 30.0, 10.0, 5.0)
        
        # --- Example: Throttle ESC/Motor Controller ---
        # Map velocity (e.g., -1.0 to 1.0 m/s) to a PWM duty cycle (e.g., -100 to 100)
        throttle_pwm = self.map_range(target_velocity, -1.0, 1.0, 5.0, 10.0)
        if throttle_pwm <= 8.1 and target_velocity >= 0.03:
            throttle_pwm = 8.1
        elif throttle_pwm >= 7.0 and target_velocity <= -0.03:
            throttle_pwm = 7.0
        
        # Log it so you can verify the math is working before hooking up the motors
        self.get_logger().debug(f"Cmd: v={target_velocity:.2f}, w={math.degrees(steering_angle_rad):.2f}deg | HW: Thr={throttle_pwm:.0f}, Str={steering_pwm:.0f}deg")
        print(f"Cmd: v={target_velocity:.2f}, w={math.degrees(steering_angle_rad):.2f}deg | HW: Thr={throttle_pwm:.2f}, Str={steering_pwm:.2f}")
        # Send to motors
        lgpio.tx_pwm(h, THROTTLE_PIN, PWM_FREQ, throttle_pwm) #DRIVE motor
        lgpio.tx_pwm(h, STEERING_PIN, PWM_FREQ, steering_pwm) #TURN motor



def main(args=None):
    global h
    rclpy.init(args=args)
    node = AckermannBridge()
    
    try:
        # 1. Open the GPIO Chip
        print(f"Opening GPIO Chip {CHIP_ID}...")
        h = lgpio.gpiochip_open(CHIP_ID)
        lgpio.gpio_claim_output(h, THROTTLE_PIN)
        lgpio.gpio_claim_output(h, STEERING_PIN)

        rclpy.spin(node)

    except lgpio.error as e:
        print(f"LGPIO Error: {e}")
        print("If 'chip not found', change CHIP_ID to 0.")

    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info("Shutting down. Sending kill signal to motors.")
        # Kill pwm
        lgpio.gpiochip_close(h)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()


