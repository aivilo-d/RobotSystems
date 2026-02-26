#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/ArmPi/')
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
        if max_area > 2500:  #the largest area was found
            rect = cv2.minAreaRect(areaMaxContour_max)
            box = np.int0(cv2.boxPoints(rect))

            roi = getROI(box) #get ROI region

            img_centerx, img_centery = getCenter(rect, roi, self.size, self.square_length)  #get center coordinates of the wooden block
            
            world_x, world_y = convertCoordinate(img_centerx, img_centery, self.size) #convert to real world coordinates
            
            
            cv2.drawContours(img, [box], -1, self.range_rgb[self.detected_color], 2)
            cv2.putText(img, '(' + str(world_x) + ',' + str(world_y) + ')', (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.range_rgb[self.detected_color], 1) #draw the center point
        return img

    def track(self, img):
        frame_lab = self.get_image(img)
        areaMaxContour_max, max_area = self.find_contours(frame_lab)
        img = self.find_block(img, areaMaxContour_max, max_area)
        return img

if __name__ == '__main__':
    my_camera = Camera.Camera()
    my_camera.camera_open()
    tracker = Tracker(my_camera)
    while True:
        img = tracker.camera.frame
        if img is not None:
            frame = img.copy()
            Frame = tracker.track(frame)           
            cv2.imshow('Frame', Frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
    my_camera.camera_close()
    cv2.destroyAllWindows()
    