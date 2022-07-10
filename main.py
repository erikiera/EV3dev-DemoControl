#!/usr/bin/env python3

# Based on the excellent tutorial from Anton Vanhoucke
# See:
# - https://www.ev3dev.org/docs/tutorials/using-ps3-sixaxis/
# - https://antonsmindstorms.com/2019/04/24/how-to-connec-a-ps3-sixaxis-gamepad-to-an-ev3-brick/
# - https://antonsmindstorms.com/

# Note: This does not use the MicroPython implementation. It uses ev3dev2-Python on Python3

__author__ = 'Anton Vanhoucke'
__author__ = 'Erik Anderson'

import evdev
import ev3dev2.auto as ev3
import ev3dev2.motor
import ev3dev2
import threading
from sys import stderr
#import os.system

    # Type: 1
    #   Codes:
    #       311 right bumper
    #       313 right trigger
    #       310 left bumper
    #       312 left trigger
    #   https://antonsmindstorms.com/2019/04/24/how-to-connec-a-ps3-sixaxis-gamepad-to-an-ev3-brick/

    #   Logitech F710 codes:
    #       311 right bumper
    #       Stick: 5 right trigger
    #       310 left bumper
    #       Stick: 2 left trigger
    #       3 right stick x
    #       4 right stick y
    #       0 left stick x
    #       1 left stick y

speed = 0
speedFront = 0
speedRear = 0
turnSpeed = 0
steering = 0
running = True
turning = False
invertDrive = 1
scaleLow = 0
scaleHigh = 255

## Some helpers ##
def scale(val, src, dst):
    """
    Scale the given value from the scale of src to the scale of dst.
    -- val: float or int
    -- src: tuple
    -- dst: tuple
    """
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scale_stick(value):
    # stickPosition = scale(value,(0,255),(-100,100))
    #stickPosition = scale(value,(0,255),(-50,50))
    stickPosition = scale(value,(scaleLow, scaleHigh),(-100,100))
    if abs(stickPosition) < 15:
        return 0
    else:
        return stickPosition

class MotorThread(threading.Thread):
    def __init__(self):      
        try:
            self.motorFront = ev3.MediumMotor(ev3.OUTPUT_A)
            self.FRONT_MOTOR_PRESENT=True
        except:
            print('No motor found in port A', file=stderr)
            self.FRONT_MOTOR_PRESENT=False
        try:
            self.motorRear = ev3.MediumMotor(ev3.OUTPUT_D)
            self.REAR_MOTOR_PRESENT=True
        except:
            print('No motor found in port D', file=stderr)
            self.REAR_MOTOR_PRESENT=False
        self.drive = ev3.MoveSteering(ev3.OUTPUT_C, ev3.OUTPUT_B)
        self.tank = ev3.MoveTank(ev3.OUTPUT_C, ev3.OUTPUT_B)

        threading.Thread.__init__(self)

    def run(self):
        print("Engine running!")
        # os.system('espeak "I am ready."')
        while running:
            self.drive.on(steering*invertDrive, speed*0.3 * invertDrive)
            if self.FRONT_MOTOR_PRESENT:
                self.motorFront.on(speedFront*0.2)
            if self.REAR_MOTOR_PRESENT:
                self.motorRear.on(speedRear*0.2)
            # If we are turning in place, don't do anything else...
            while turning:
                self.tank.on(turnSpeed*0.5, -turnSpeed*0.5)

        self.drive.stop()
        self.motorRight.stop()
        self.motorleft.stop()


## Initializing ##
print("Finding controller...", file=stderr)
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
for device in devices:
    print("Device:  ", device.name, file=stderr)
    if device.name == 'Logitech Gamepad F710':
        controller = device.fn
        scaleLow = 32768
        scaleHigh = -32768
        print(device.name, " found.", file=stderr)
    if device.name == 'PLAYSTATION(R)3 Controller':
        controller = device.fn
        scaleLow = 0
        scaleHigh = 255
        print(device.name, " found.", file=stderr)
gamepad = evdev.InputDevice(controller)



motor_thread = MotorThread()
motor_thread.setDaemon(True)
motor_thread.start()

print("Ready to drive!!", file=stderr)

for event in gamepad.read_loop():   #this loops infinitely
    # Analog stick actions:
    if event.type == 3:            #A stick is moved
        #print("Stick action: ", event.code, "  Value: ", event.value, file=stderr)
        if event.code == 1:         #Y axis on Left stick
            speed = -1 * scale_stick(event.value)
        if event.code == 0:         # X axis on the Left stick
            steering = scale_stick(event.value)
        if event.code == 3:         # X axis on the Right stick
            if abs(scale_stick(event.value)) < 20:
                turning = False
            else:
                turning = True
                turnSpeed = scale_stick(event.value) * 0.4 * invertDrive
        if event.code == 2:         # Left trigger
            if event.value > 10:
                speedRear = 200
            else:
                speedRear = 0
        if event.code == 5:         # Right trigger
            if event.value > 10:
                speedFront = 200
            else:
                speedFront = 0

    # Button/key presses:
    if event.type == 1:
        #print("Button pressed: ", event.code, file=stderr)
        # Right side -> Front Motor
        if event.code == 311:       # Right Bumper - Controls Motor A
            if event.value == 1:
                speedFront = -200
            else:
                speedFront = 0
        if event.code == 313:       # Right Trigger - Controls Motor A
            if event.value == 1:
                speedFront = 200
            else:
                speedFront = 0
        # Left Side -> Rear Motor
        if event.code == 310:       # Left Bumper - Controls Motor D
            if event.value == 1:
                speedRear = -200
            else:
                speedRear = 0
        if event.code == 312:       # Left Trigger - Controls Motor D
            if event.value == 1:
                speedRear = 200
            else:
                speedRear = 0
        if event.code == 314:       # Select button - Inverts the direction the robot drives
            if event.value == 1:
                invertDrive = invertDrive * -1      # Invert forward/backward drive
        if event.code == 315 and event.value == 1:  # Start Button
            pass
            print("START button is pressed. Stopping.", file=stderr)
            running = False
            break
    