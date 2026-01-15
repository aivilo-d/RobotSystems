from picarx_improved import Picarx
import time

def move_forward(car, speed=50, angle=0):
    car.set_dir_servo_angle(angle)
    car.forward(speed)

def move_backward(car, speed=50, angle=0):
    car.set_dir_servo_angle(angle)
    car.backward(speed)

def parallel_right(car, speed=50, angle=30):
    car.set_dir_servo_angle(angle)
    car.backward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(-angle)
    car.backward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(0)
    car.forward(speed)
    time.sleep(1)


def parallel_left(car, speed=50, angle=30):
    car.set_dir_servo_angle(-angle)
    car.backward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(angle)
    car.backward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(0)
    car.forward(speed)
    time.sleep(1)

def k_right(car, speed=50, angle=30):
    car.set_dir_servo_angle(angle)
    car.forward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(-angle)
    car.backward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(angle)
    car.forward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(0)
    car.forward(speed)
    time.sleep(1)

def k_left(car, speed=50, angle=30):
    car.set_dir_servo_angle(-angle)
    car.forward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(angle)
    car.backward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(-angle)
    car.forward(speed)
    time.sleep(2)
    car.set_dir_servo_angle(0)
    car.forward(speed)
    time.sleep(1)

if __name__ == "__main__":
    car = Picarx()

    maneuver = input("Choose a manuever: ")

    if maneuver == "move forward":
        move_forward(car)
    if maneuver == "move backward":
        move_backward(car)
    if maneuver == "parallel right":
        parallel_right(car)
    if maneuver == "parallel left":
        parallel_left(car)
    if maneuver == "k right":
        k_right(car)
    if maneuver == "k left":
        k_left(car)

    time.sleep(2)
    car.stop()