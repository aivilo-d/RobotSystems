from picarx_improved import Picarx
import time

class Sensor(object):

    def __init__(self, sensor):
        self.sensor = sensor
        self.pins = self.sensor.pins
        self.sensor_reading = None
    
    def read(self):
        self.sensor_reading = self.sensor.read()
        return self.sensor_reading
    
class Interpreter(object):

    def __init__(self, sensitivity = 0, polarity = 0):
        #sensitvity is the threshold to recognize a difference between light and dark
        self.sensitivity = sensitivity
        #polarity of 0 means dark line, polarity of 1 means light line
        self.polarity = polarity
        self.relative_position = None
    
    def process(self, sensor_reading):
        
        if self.polarity == 0:
            #dark line case, turn towards the dark
            #find if left or right is smaller
            #turn towards that side in proportion to how dark or light it is
            min_index = sensor_reading.index(min(sensor_reading))
            if min_index == 0:
                self.relative_position = -1 #i should eventually figure out how to scale this
            if min_index == 1:
                self.relative_position = 0
            if min_index == 2:
                self.relative_position = 1
            
        if self.polarity == 1:
            #light line case, turn towards the light
            #find if left or right is bigger
            #turn towards that side in proportion to how dark or light it is
            max_index = sensor_reading.index(max(sensor_reading))
            if max_index == 0:
                self.relative_position = -1 #i should eventually figure out how to scale this
            if max_index == 1:
                self.relative_position = 0
            if max_index == 2:
                self.relative_position = 1
        return self.relative_position
            
class Controller(object):

    def __init__(self, scaling_factor = 1):
        self.scaling_factor = scaling_factor
    
    def control(self, relative_position):
        angle = relative_position * 30 * self.scaling_factor
        car.set_dir_servo_angle(angle)
        car.forward(50)
        return angle

        
if __name__ == "__main__":
    car = Picarx()
    sensor = Sensor(car.grayscale)
    interpreter = Interpreter()
    controller = Controller()

    while 1==1:
        sensor.read()
        interpreter.process(sensor.sensor_reading)
        controller.control(interpreter.relative_position)
        time.sleep(.25)

    car.stop()