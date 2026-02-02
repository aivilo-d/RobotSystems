from time import sleep
from picarx_improved import Picarx
import cv2
from picamera2 import Picamera2
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from readerwriterlock import rwlock

picam2 = Picamera2()
picam2.preview_configuration.main.size = (1280, 720) # Set desired resolution
picam2.preview_configuration.main.format = "RGB888" # Use RGB format for compatibility with OpenCV
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

#define shutdown event
shutdown_event = Event()

#Exception handle function
def handle_exception(future):
    exception = future.exception()
    if exception:
        print(f'Exception in worker thread: {exception}')

def sensor_function(picam2, sensor_bus, sensor_delay):
    while not shutdown_event.is_set():
        im = picam2.capture_array()
        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        im = cv2.bitwise_not(im) #invert the image to make the line light instead of dark
        ret, thresh = cv2.threshold(im, 127, 255, 0)
        cnts, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        C = None
        if cnts is not None and len(cnts) > 0:
            C = max(cnts, key = cv2.contourArea)
        if C is None:
            return None, None
        M = cv2.moments(C)
        cx = int(M['m10']/M['m00'])
        sensor_bus.write(cx)
        sleep(sensor_delay)
    raise Exception('Sensor raised an excpetion')

def interpretor_function(sensor_bus, interpretor_bus, interpretor_delay):
    while not shutdown_event.is_set():
        target = sensor_bus.read()
        relative_position = (target - 640) / 640
        interpretor_bus.write(relative_position)
        sleep(interpretor_delay)
    raise Exception('Interpretor raised an excpetion')

def control_function(car, interpretor_bus, control_delay):
    while not shutdown_event.is_set():
        relative_position = interpretor_bus.read()
        angle = relative_position * 70
        car.set_dir_servo_angle(angle)
        car.forward(30)
        sleep(control_delay)
    raise Exception('Controller raised an excpetion')

    
class Buss(object):
    
    def __init__(self, message):
        self.lock = rwlock.RWLockWriteD()
        self.message = message
    
    def write(self, message):
        with self.lock.gen_wlock():
            self.message = message
    
    def read(self):
        with self.lock.gen_rlock():
            message = self.message
        return message
    
        
if __name__ == "__main__":
    car = Picarx()
    sensor_bus = Buss(640)
    interpretor_bus = Buss(0)
    car.set_cam_tilt_angle(-45)

    futures = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        for i in range(3):
            #Spawn task threads
            eSensor = executor.submit(sensor_function, picam2, sensor_bus, .05)
            eInterpretor = executor.submit(interpretor_function, sensor_bus, interpretor_bus, .05)
            eController = executor.submit(control_function, car, interpretor_bus, .05)
            #Add exception callback
            eSensor.add_done_callback(handle_exception)
            eInterpretor.add_done_callback(handle_exception)
            eController.add_done_callback(handle_exception)
            futures.append(eSensor, eInterpretor, eController)

        try:
            #Keep the main thread running to response for the kill signal
            while not shutdown_event.is_set():
                sleep(1)
        except KeyboardInterrupt:
            #Trigger the shutdown even when recieve the kill signal
            print('Shutting down')
            shutdown_event.set()
        finally:
            #Ensure all threads finish
            executor.shutdown()
