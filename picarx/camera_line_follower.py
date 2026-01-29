from picarx_improved import Picarx
import time
import cv2
from picamera2 import Picamera2
import numpy as np

picam2 = Picamera2()
picam2.preview_configuration.main.size = (1280, 720) # Set desired resolution
picam2.preview_configuration.main.format = "RGB888" # Use RGB format for compatibility with OpenCV
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

class Sensor(object):

    def __init__(self, cam, polarity = 0):
        self.cam = cam
        #polarity of 0 means dark line, polarity of 1 means light line
        self.polarity = polarity
        self.target = None
        
    def find_target(self, T=127):
        im = self.cam.capture_array()
        gray_im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        if self.polarity == 0:
            im = cv2.bitwise_not(gray_im) #invert the image to make the line light instead of dark
        ret, thresh = cv2.threshold(im, T, 255, cv2.THRESH_BINARY)
        im2, cnts, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        C = None
        if cnts is not None and len(cnts) > 0:
            C = max(cnts, key = cv2.contourArea)
        if C is None:
            return None, None
        M = cv2.moments(C)
        cx = int(M['m10']/M['m00'])
        self.target = cx
        return cx
        
        
    
class Interpreter(object):

    def __init__(self):
        self.relative_position = None
    
    def process(self, target):
        self.relative_positon = (target - 640) / 640
        return self.relative_position
            
class Controller(object):

    def __init__(self, scaling_factor = 1):
        self.scaling_factor = scaling_factor
    
    def control(self, relative_position):
        angle = relative_position * 70 * self.scaling_factor
        car.set_dir_servo_angle(angle)
        car.forward(30)
        return angle

        
if __name__ == "__main__":
    car = Picarx()
    camera = Sensor(picam2)
    interpreter = Interpreter()
    controller = Controller()

    while 1==1:
        camera.find_target()
        interpreter.process(camera.target)
        controller.control(interpreter.relative_position)
        time.sleep(.05)

    car.stop()
