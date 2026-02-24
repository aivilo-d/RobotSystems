import sys
sys.path.append('/home/pi/ArmPi/')
import time
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board

AK = ArmIK()

class Mover():

    def __init__(self):
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
        AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)

    def setBuzzer(timer):
        Board.setBuzzer(0)
        Board.setBuzzer(1)
        time.sleep(timer)
        Board.setBuzzer(0)

    def sort(self, world_X, world_Y, detect_color):  
        self.detect_color = detect_color      
        if self.detect_color != 'None':
            self.setBuzzer(0.1)
            result = AK.setPitchRangeMoving((world_X, world_Y, 7), -90, -90, 0)  
            if result == False:
                return False
            else:
                time.sleep(result[2]/1000) #If the specified location can be reached, obtain the running time.

                servo2_angle = getAngle(world_X, world_Y, self.rotation_angle) #Calculate the angle that the gripper needs to rotate.
                Board.setBusServoPulse(1, self.servo1 - 280, 500)  # claws open
                Board.setBusServoPulse(2, servo2_angle, 500)
                time.sleep(0.5)
                    
                AK.setPitchRangeMoving((world_X, world_Y, 1.5), -90, -90, 0, 1000)
                time.sleep(1.5)

                Board.setBusServoPulse(1, self.servo1, 500)  #Clamp closing
                time.sleep(0.8)

                Board.setBusServoPulse(2, 500, 500)
                AK.setPitchRangeMoving((world_X, world_Y, 12), -90, -90, 0, 1000)  #Robotic arm raised
                time.sleep(1)

                result = AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], 12), -90, -90, 0)   
                time.sleep(result[2]/1000)
                                     
                servo2_angle = getAngle(self.coordinate[detect_color][0], self.coordinate[detect_color][1], -90)
                Board.setBusServoPulse(2, servo2_angle, 500)
                time.sleep(0.5)

                AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], coordinate[detect_color][2] + 3), -90, -90, 0, 500)
                time.sleep(0.5)
                                      
                AK.setPitchRangeMoving((self.coordinate[detect_color]), -90, -90, 0, 1000)
                time.sleep(0.8)

                Board.setBusServoPulse(1, self.servo1 - 200, 500)  # The claws open, and the object is placed down.
                time.sleep(0.8)

                AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], 12), -90, -90, 0, 800)
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
            result = AK.setPitchRangeMoving((world_X, world_Y, 7), -90, -90, 0)  # 移到目标位置，高度5cm
            if result == False:
                return False
            else:
                time.sleep(result[2]/1000)

                # 计算夹持器需要旋转的角度
                servo2_angle = getAngle(world_X, world_Y, self.rotation_angle)
                Board.setBusServoPulse(1, self.servo1 - 280, 500)  # 爪子张开
                Board.setBusServoPulse(2, servo2_angle, 500)
                time.sleep(0.5)

                AK.setPitchRangeMoving((world_X, world_Y, 2), -90, -90, 0, 1000)  # 降低高度到2cm
                time.sleep(1.5)

                Board.setBusServoPulse(1, self.servo1, 500)  # 夹持器闭合
                time.sleep(0.8)

                Board.setBusServoPulse(2, 500, 500)
                AK.setPitchRangeMoving((world_X, world_Y, 12), -90, -90, 0, 1000)  # 机械臂抬起
                time.sleep(1)

                AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], 12), -90, -90, 0, 1500) 
                time.sleep(1.5)
                                     
                servo2_angle = getAngle(self.coordinate[detect_color][0], self.coordinate[detect_color][1], -90)
                Board.setBusServoPulse(2, servo2_angle, 500)
                time.sleep(0.5)

                AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], z + 3), -90, -90, 0, 500)
                time.sleep(0.5)
                                 
                AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], z), -90, -90, 0, 1000)
                time.sleep(0.8)

                Board.setBusServoPulse(1, self.servo1 - 200, 500)  # 爪子张开  ，放下物体
                time.sleep(1)

                AK.setPitchRangeMoving((self.coordinate[detect_color][0], self.coordinate[detect_color][1], 12), -90, -90, 0, 800)
                time.sleep(0.8)

                self.initMove()  # 回到初始位置
                time.sleep(1.5)

                detect_color = 'None'