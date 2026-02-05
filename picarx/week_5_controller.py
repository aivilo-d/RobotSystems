from time import sleep
from picarx_improved import Picarx
import cv2
from picamera2 import Picamera2
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from readerwriterlock import rwlock
import rossros

picam2 = Picamera2()
picam2.preview_configuration.main.size = (1280, 720) # Set desired resolution
picam2.preview_configuration.main.format = "RGB888" # Use RGB format for compatibility with OpenCV
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

car = Picarx()

def camera_function():
    print("run sense")
    im = picam2.capture_array()
    im = im[700:720, 0:1280]
    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im = cv2.bitwise_not(im) #invert the image to make the line light instead of dark
    ret, thresh = cv2.threshold(im, 127, 255, cv2.THRESH_BINARY)
    cnts, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    C = None
    if cnts is not None and len(cnts) > 0:
        C = max(cnts, key = cv2.contourArea)
    if C is not None:
        M = cv2.moments(C)
        if M['m00'] != 0:
            cx = int(M['m10']/M['m00'])
            return cx
    else:
        print("C is NONE")

def ultrasonic_function():
    reading = car.ultrasonic.read()
    return reading

def camera_interpretor_function(cx):
    print("run interpret")
    relative_position = (cx - 640) / 640 #this keeps erroring because cx is None I think
    return relative_position

def ultrasonic_interpretor_function(reading):
    if reading == -1:
        return  1 #this keeps driving but should just continue same behaviour
    if reading == -2:
        return 1 #this keeps driving but should just continue same behaviour
    if reading < 5:
        return 0
    else:
        return 1

def camera_only_control(relative_position):
    print("run control")
    angle = relative_position * 70
    car.set_dir_servo_angle(angle)
    car.forward(30)

def control_function(relative_position, distance):
    if distance == 0:
       car.forward(0) 
    else:
        angle = relative_position * 70
        car.set_dir_servo_angle(angle)
        car.forward(30)
    
    
        
if __name__ == "__main__":
    
    consumer_producer_list = []

    termination_bus = rossros.Bus(initial_message=0, name="Termination Bus")
    camera_bus = rossros.Bus(640,"Camera Bus")
    camera_interpretor_bus = rossros.Bus(0,"Camera Interpretor Bus")
    
    ultrasonic_bus = rossros.Bus(640,"Ultrasonic Bus")
    ultrasonic_interpretor_bus = rossros.Bus(0,"Ultrasonic Interpretor Bus")

    timer = rossros.Timer(termination_bus,  # buses that receive the countdown value
                 duration=5,  # how many seconds the timer should run for (0 is forever)
                 delay=0,  # how many seconds to sleep for between checking time
                 termination_buses=termination_bus,
                 name="termination timer")
    camera_sensor = rossros.Producer(camera_function, camera_bus, .05, termination_bus,"Camera Sensor")
    camera_interpretor = rossros.ConsumerProducer(camera_interpretor_function, camera_bus, camera_interpretor_bus, .05, termination_bus, "Camera Interpretor")
    #camera_controller = rossros.Consumer(camera_only_control, camera_interpretor_bus, .05, termination_bus,"Camera Controller")
   
    ultrasonic_sensor = rossros.Producer(ultrasonic_function, ultrasonic_bus, .05, termination_bus,"Ultrasonic Sensor")
    ultrasonic_interpretor = rossros.ConsumerProducer(ultrasonic_interpretor_function, ultrasonic_bus, ultrasonic_interpretor_bus, .05, termination_bus, "Ultrasonic Interpretor")
    controller = rossros.Consumer(control_function, (camera_interpretor_bus, ultrasonic_interpretor_bus), .05, termination_bus,"Controller")
    
    #consumer_producer_list = ([timer, camera_sensor, camera_interpretor, camera_controller])
    consumer_producer_list = ([timer, camera_sensor, ultrasonic_sensor, camera_interpretor, ultrasonic_interpretor, controller])

    car.set_cam_tilt_angle(-45)

    rossros.runConcurrently(consumer_producer_list)
