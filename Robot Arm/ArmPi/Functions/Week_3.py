import sys
sys.path.append('/home/pi/ArmPi/')
import time
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
import cv2
import Camera
import math
import numpy as np
from ArmIK.Transform import *

class Tracker():
    
    def __init__(self, camera, target_color = ('red', 'green', 'blue'), size = (640, 480)):
        self.target_color = target_color
        self.camera = camera
        self.size = size
        self.square_length = 3
        self.detected_color = None
        self.color_range = {
        'red': [(0, 151, 100), (255, 255, 255)], 
        'green': [(0, 0, 0), (255, 115, 255)], 
        'blue': [(0, 0, 0), (255, 255, 110)], 
        'black': [(0, 0, 0), (56, 255, 255)], 
        'white': [(193, 0, 0), (255, 250, 255)], 
        }
        self.range_rgb = {
        'red': (0, 0, 255),
        'blue': (255, 0, 0),
        'green': (0, 255, 0),
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        }

    def getAreaMaxContour(self, contours):
        contour_area_temp = 0
        contour_area_max = 0
        area_max_contour = None
        for c in contours:  # Traversing all contours
            contour_area_temp = math.fabs(cv2.contourArea(c))  # Calculate contour area
            if contour_area_temp > contour_area_max:
                contour_area_max = contour_area_temp
                if contour_area_temp > 300:  # The contour of the largest area is only effective when the area is greater than 300, in order to filter out interference
                    area_max_contour = c
        return area_max_contour, contour_area_max 

    def get_image(self, img):
        img_copy = img.copy()
        img_h, img_w = img.shape[:2]
        cv2.line(img, (0, int(img_h / 2)), (img_w, int(img_h / 2)), (0, 0, 200), 1)
        cv2.line(img, (int(img_w / 2), 0), (int(img_w / 2), img_h), (0, 0, 200), 1)
        frame_resize = cv2.resize(img_copy, self.size, interpolation=cv2.INTER_NEAREST)
        frame_gb = cv2.GaussianBlur(frame_resize, (11, 11), 11)
        frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)
        return frame_lab

    def find_contours(self, frame_lab):
        areaMaxContour_max = 0
        max_area = 0
        for i in self.color_range:
            if i in self.target_color:
                frame_mask = cv2.inRange(frame_lab, self.color_range[i][0], self.color_range[i][1])  #perform bitwise operations on original image and mask
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((6, 6), np.uint8))  #opening operation
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((6, 6), np.uint8))  #closing operation
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  #find the outline
                areaMaxContour, area_max = self.getAreaMaxContour(contours)
                if areaMaxContour is not None:
                    if area_max > max_area:#找最大面积 find the largest area
                        max_area = area_max
                        self.detected_color = i
                        areaMaxContour_max = areaMaxContour 
        return areaMaxContour_max, max_area
    
    def find_block(self, img, areaMaxContour_max, max_area):
        world_x = None
        world_y = None
        if max_area > 2500:  #the largest area was found
            rect = cv2.minAreaRect(areaMaxContour_max)
            box = np.int0(cv2.boxPoints(rect))

            roi = getROI(box) #get ROI region

            img_centerx, img_centery = getCenter(rect, roi, self.size, self.square_length)  #get center coordinates of the wooden block
            
            world_x, world_y = convertCoordinate(img_centerx, img_centery, self.size) #convert to real world coordinates
            
            
            cv2.drawContours(img, [box], -1, self.range_rgb[self.detected_color], 2)
            cv2.putText(img, '(' + str(world_x) + ',' + str(world_y) + ')', (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.range_rgb[self.detected_color], 1) #draw the center point
        return img, world_x, world_y

    def track(self, img):
        frame_lab = self.get_image(img)
        areaMaxContour_max, max_area = self.find_contours(frame_lab)
        img, world_x, world_y = self.find_block(img, areaMaxContour_max, max_area)
        return img, world_x, world_y, self.detected_color

class Mover():

    def __init__(self, AK):
        self.AK = AK
        self.coordinate = {
            'red':   (-15 + 0.5, 12 - 0.5, 1.5),
            'green': (-15 + 0.5, 6 - 0.5,  1.5),
            'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
            }
        self.servo1 = 500
        self.detect_color = None
        self.rotation_angle = 0
        self.dz = 2.5

    def initMove(self):
        Board.setBusServoPulse(1, self.servo1 - 50, 300)
        Board.setBusServoPulse(2, 500, 500)
        self.AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)

    def Buzzer(self, timer):
        Board.setBuzzer(0)
        Board.setBuzzer(1)
        time.sleep(timer)
        Board.setBuzzer(0)

    def sort(self, world_X, world_Y, detect_color):  
        self.detect_color = detect_color      
        if self.detect_color != 'None':
            self.Buzzer(0.1)
            result = self.AK.setPitchRangeMoving((world_X, world_Y, 7), -90, -90, 0)  
            if result == False:
                return False
            else:
                time.sleep(result[2]/1000) #If the specified location can be reached, obtain the running time.

                servo2_angle = getAngle(world_X, world_Y, self.rotation_angle) #Calculate the angle that the gripper needs to rotate.
                Board.setBusServoPulse(1, self.servo1 - 280, 500)  # claws open
                Board.setBusServoPulse(2, servo2_angle, 500)
                time.sleep(0.5)
                    
                self.AK.setPitchRangeMoving((world_X, world_Y, 1.5), -90, -90, 0, 1000)
                time.sleep(1.5)

                Board.setBusServoPulse(1, self.servo1, 500)  #Clamp closing
                time.sleep(0.8)

                Board.setBusServoPulse(2, 500, 500)
                self.AK.setPitchRangeMoving((world_X, world_Y, 12), -90, -90, 0, 1000)  #Robotic arm raised
                time.sleep(1)

                result = self.AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], 12), -90, -90, 0)   
                time.sleep(result[2]/1000)
                                     
                servo2_angle = getAngle(self.coordinate[detect_color][0], self.coordinate[detect_color][1], -90)
                Board.setBusServoPulse(2, servo2_angle, 500)
                time.sleep(0.5)

                self.AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], self.coordinate[detect_color][2] + 3), -90, -90, 0, 500)
                time.sleep(0.5)
                                      
                self.AK.setPitchRangeMoving((self.coordinate[detect_color]), -90, -90, 0, 1000)
                time.sleep(0.8)

                Board.setBusServoPulse(1, self.servo1 - 200, 500)  # The claws open, and the object is placed down.
                time.sleep(0.8)

                self.AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], 12), -90, -90, 0, 800)
                time.sleep(0.8)

                self.initMove()  # Return to initial position
                time.sleep(1.5)

                detect_color = 'None'

    def pallet(self, world_X, world_Y, detect_color):
        self.detect_color = detect_color
        if detect_color != 'None':
            self.setBuzzer(0.1)
            # 高度累加
            z = z_r
            z_r += self.dz
            if z == 2 * self.dz + self.coordinate['red'][2]:
                z_r = self.coordinate['red'][2]
            if z == self.coordinate['red'][2]:  
                #move_square = True
                time.sleep(3)
                #move_square = False
            result = self.AK.setPitchRangeMoving((world_X, world_Y, 7), -90, -90, 0)  # 移到目标位置，高度5cm
            if result == False:
                return False
            else:
                time.sleep(result[2]/1000)

                # 计算夹持器需要旋转的角度
                servo2_angle = getAngle(world_X, world_Y, self.rotation_angle)
                Board.setBusServoPulse(1, self.servo1 - 280, 500)  # 爪子张开
                Board.setBusServoPulse(2, servo2_angle, 500)
                time.sleep(0.5)

                self.AK.setPitchRangeMoving((world_X, world_Y, 2), -90, -90, 0, 1000)  # 降低高度到2cm
                time.sleep(1.5)

                Board.setBusServoPulse(1, self.servo1, 500)  # 夹持器闭合
                time.sleep(0.8)

                Board.setBusServoPulse(2, 500, 500)
                self.AK.setPitchRangeMoving((world_X, world_Y, 12), -90, -90, 0, 1000)  # 机械臂抬起
                time.sleep(1)

                self.AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], 12), -90, -90, 0, 1500) 
                time.sleep(1.5)
                                     
                servo2_angle = getAngle(self.coordinate[detect_color][0], self.coordinate[detect_color][1], -90)
                Board.setBusServoPulse(2, servo2_angle, 500)
                time.sleep(0.5)

                self.AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], z + 3), -90, -90, 0, 500)
                time.sleep(0.5)
                                 
                self.AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], z), -90, -90, 0, 1000)
                time.sleep(0.8)

                Board.setBusServoPulse(1, self.servo1 - 200, 500)  # 爪子张开  ，放下物体
                time.sleep(1)

                self.AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], 12), -90, -90, 0, 800)
                time.sleep(0.8)

                self.initMove()  # 回到初始位置
                time.sleep(1.5)

                detect_color = 'None'

if __name__ == '__main__':
    my_camera = Camera.Camera()
    my_camera.camera_open()
    tracker = Tracker(my_camera)
    AK = ArmIK()
    mover = Mover(AK)
    while True:
        img = tracker.camera.frame
        if img is not None:
            frame = img.copy()
            Frame, world_x, world_y, detected_color = tracker.track(frame)           
            cv2.imshow('Frame', Frame)
            mover.sort(world_x, world_y, detected_color)
            key = cv2.waitKey(1)
            if key == 27:
                break
    my_camera.camera_close()
    cv2.destroyAllWindows()