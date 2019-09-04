#Libraries
import RPi.GPIO as GPIO
import time
import serial
import multiprocessing
import os
import smbus

#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BOARD)
 
#set GPIO Pins
GPIO_TRIGGER = 12
GPIO_ECHO = 18
pir = 16
led = 11 

#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(pir, GPIO.IN)
GPIO.setup( led, GPIO.OUT)

time.sleep(2)

data = serial.Serial(
                    port='/dev/ttyAMA0',
                    baudrate = 9600,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS
                    )
                    #timeout=1 # must use when using data.readline()
                    #)
# Define some constants from the datasheet of digital light sensor
DEVICE     = 0x23 # Default device I2C address
POWER_DOWN = 0x00 # No active state
POWER_ON   = 0x01 # Power on
RESET      = 0x07 # Reset data register value
# Start measurement at 4lx resolution. Time typically 16ms.
CONTINUOUS_LOW_RES_MODE = 0x13
# Start measurement at 1lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Start measurement at 0.5lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Start measurement at 0.5lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_LOW_RES_MODE = 0x23
#bus = smbus.SMBus(0) # Rev 1 Pi uses 0
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1

# 50Hz PWM Frequency  
pwm_led = GPIO.PWM( led, 50)  
# Full Brightness, 100% Duty Cycle  
pwm_led.start(100)

def distance():
    GPIO.output(GPIO_TRIGGER, True) #set Trigger to HIGH
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False) #set Trigger after 0.01ms to LOW
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    TimeElapsed = StopTime - StartTime #time difference between start and arrival
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance

def rfid_check(check):
    #function to read from the EM18 rfid reader
    x=data.read(12)#read rfid card number

    if x=="0900962E09B8":
        print "Card No - ",x
        check.value = check.value*(-1)
        return
    else:
        print "Card No - ",x
        print "Wrong Card....."
        return

def convertToNumber(data):
    # Simple function to convert 2 bytes of data
    # into a decimal number. Optional parameter 'decimals'
    # will round to specified number of decimal places.
    result=(data[1] + (256 * data[0])) / 1.2
    return (result)

def readLight(addr=DEVICE):
    # Read data from I2C interface
    data = bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
    return convertToNumber(data)

if __name__ == '__main__':
    try:
        session_duration = int(raw_input("Please Choose Your Session Duration (min)"))
        session_duration = session_duration * 60 #converting into seconds
        check = multiprocessing.Value('i', -1) #shared variable between parallel processes whose value define whether the cubicle is locked/unlocked 
        while True:
            pwm_led.ChangeDutyCycle(0)
            p = multiprocessing.Process(target=rfid_check, args=(check,)) #run process p in parallel in separate core
            p.start() #start process p
            os.system('espeak "Place Your Card on the scanner" 2>/dev/null') #speaker output
            print ("Place Your card on the Scanner")
            while True:
                if GPIO.input(pir): #Check whether pir is HIGH
                    os.system('espeak "Intruder Detected" 2>/dev/null') #speaker output
                    print ("Intruder Detected")
                    lightLevel = readLight() #read data from the digital light sensor
                    if lightLevel < 20: #if it is too dark turn on the leds and then capture photo
                        pwm_led.ChangeDutyCycle(95)
                    os.system('mkdir /home/pi/QBKL/photos/$(date +%d_%m_%y)') # makes new directory to save captured photo
                    os.system('fswebcam -p YUYV -d /dev/video0 -r 640x480 /home/pi/QBKL/photos/%d_%m_%y/%H_%M_%S.jpeg') # uses Fswebcam to take picture
                    pwm_led.ChangeDutyCycle(0)
                    time.sleep(3)
                if check.value == 1: #cubicle unlocked
                    break
            p.join() #wait for process p to finish
            p = multiprocessing.Process(target=rfid_check, args=(check,)) #run process p in parallel in separate core
            p.start()

            counter = 1000
            start = time.time() #time when the user logs into the cubicle
            while True:
                lightLevel = readLight() #read data from the digital light sensor
                print("Light Level : " + format(lightLevel,'.2f') + " lx")
                lightLevel= int(lightLevel/3)
                if lightLevel > 100: #lightLevel must be in range 0-100
                    lightLevel = 100;
                lightLevel = 100 - lightLevel #higher the surrounding light dimmer should be the leds
                pwm_led.ChangeDutyCycle(lightLevel)  
                
                dist = distance()#measure the distance from ping sensor
                print ("Measured Distance = %.1f cm" % dist)
                
                if GPIO.input(pir): #Check whether pir is HIGH 
                    time.sleep(0.1)#D1- Delay to avoid multiple detection
                    print("Detected") 
                time.sleep(0.5)
                
                counter = 1000 #iteration variable
                while True:
                    dist = int(distance())
                    if (dist < 100 or GPIO.input(pir)) and counter%10 == 0: #user detected 
                        break
                    if counter == 0: #user undetected for too long
                        break
                    if check.value == -1: #user logs out
                        break
                    counter = counter - 1
                if counter == 0:
                    break
                if check.value == -1:
                    break
                
                stop = time.time()
                if stop - start > session_duration:
                    aa = raw_input("We recommend a break. Would you wish to take a break (y/n)")
                    if aa == "y":
                        print("Successfully locked out of system")
                        os.system('espeak "Successfully locked out of system" 2>/dev/null') #speaker output
                        counter = 0
                        break
                    if aa == "n":
                        start = time.time() #update start time
            
            if counter == 0:
                check.value = -1 #cubicle locked
                p.terminate() #terminate process p
            else:
                p.join() #wait for process p to finish
            
            time.sleep(3)
                
 
    # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Stopped by User")
        data.close() #close the rfid connection
    finally:
        GPIO.cleanup() #cleanup the ports in use

