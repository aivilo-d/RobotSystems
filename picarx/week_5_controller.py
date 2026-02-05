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

def sensor_function(picam2, sensor_bus, sensor_delay):
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
    if C:
        M = cv2.moments(C)
        if M['m00'] != 0:
            cx = int(M['m10']/M['m00'])
            sensor_bus.write(cx)
        sleep(sensor_delay)
    else:
        print("C is NONE")

def interpretor_function(sensor_bus, interpretor_bus, interpretor_delay):
    print("run interpret")
    target = sensor_bus.read()
    relative_position = (target - 640) / 640
    interpretor_bus.write(relative_position)
    sleep(interpretor_delay)

def control_function(car, interpretor_bus, control_delay):
    print("run control")
    relative_position = interpretor_bus.read()
    angle = relative_position * 70
    car.set_dir_servo_angle(angle)
    car.forward(30)
    sleep(control_delay)
    
        
if __name__ == "__main__":
    
    car = Picarx()
    termination_bus = rossros.Bus(initial_message=0, name="Termination Bus")
    timer = rossros.Timer(termination_bus,  # buses that receive the countdown value
                 duration=5,  # how many seconds the timer should run for (0 is forever)
                 delay=0,  # how many seconds to sleep for between checking time
                 termination_buses=termination_bus,
                 name="termination timer")
    sensor_bus = rossros.Bus(640,"Sensor Bus")
    interpretor_bus = rossros.Bus(0,"Interpretor Bus")
    sensor = rossros.Producer(sensor_function, sensor_bus, .05, termination_bus,"Sensor")
    interpretor = rossros.ConsumerProducer(interpretor_function, sensor_bus, interpretor_bus, .05, termination_bus, "Interpretor")
    controller = rossros.Consumer(control_function, interpretor_bus, .05, termination_bus,"Controller")
    consumer_producer_list = ([timer, sensor, interpretor, controller])

    car.set_cam_tilt_angle(-45)

    rossros.runConcurrently(consumer_producer_list)
