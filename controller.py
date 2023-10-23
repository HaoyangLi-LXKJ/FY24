import map
import cbirds
import json
import websocket
import math


class Controller:
  def __init__(self, map, birds, team_id, ws):
    self.map = map
    self.birds = birds
    self.team_id = team_id
    self.ws = ws

    self.target_x = 680
    self.target_y = 1940

    # how many frame will pase after one message
    self.frame_per_message = 3

    # Last difference angle, used for PD controller
    self.last_difference_angle = 0
    self.last_turning_direction = 0
    self.difference_integral = 0

    self.truning_angle_P = 1/10
    self.turning_angle_I = 1/50
    self.truning_angle_D = 1/10

  def move_forward(self):
    print("向前移动")
    self.ws.send(json.dumps({"commandType": "goForward"}))

  def move_backward(self):
    print("向后移动")
    self.ws.send(json.dumps({"commandType": "goBack"}))

  def turn_left(self, speed):
    print("向左转动")
    self.ws.send(json.dumps({"commandType": "turnLeft", "data": speed}))

  def turn_right(self, speed):
    print("向右转动")
    self.ws.send(json.dumps({"commandType": "turnRight", "data": speed}))

  def stop_turning(self):
    print("停止转动")
    self.ws.send(json.dumps({"commandType": "steerBack"}))

  def stop_moving(self):
    # print("停止移动")
    self.ws.send(json.dumps({"commandType": "stop"}))

  def remove_skill(self):
    print("移除技能")
    self.ws.send(json.dumps({"commandType": "removeSkill"}))

  def set_attack_value(self, value):
    print("设置攻击力")
    self.ws.send(json.dumps({"commandType": "setAttackValue", "data": value}))

  def set_target_position(self, x, y):
    self.target_x = x
    self.target_y = y

  def hitting_wall_or_not(self, position_x, position_y, velocity, angle, angle_speed, moveState):
    # Array storing the upcoming frames position
    # when walk backwards, the angle should be reversed to 180du（math.pi）
    offSet = 0
    if (moveState == -1):
      offSet = math.pi
    upcoming_frames_position_x = []
    upcoming_frames_position_y = []
    upcoming_frames_position_x.append(position_x + velocity * math.cos(angle) + offSet)
    upcoming_frames_position_y.append(position_y + velocity * math.sin(angle) + offSet)
    # Calculate the upcoming frames position in self.frame_per_message
    for i in range(1, self.frame_per_message):
      upcoming_frames_position_x.append(
          upcoming_frames_position_x[i-1] + velocity * math.cos(angle + angle_speed * i) + offSet)
      upcoming_frames_position_y.append(
          upcoming_frames_position_y[i-1] + velocity * math.sin(angle+ angle_speed * i) + offSet)
    # If we are going to hit the wall(any of the upcoming frames outside the map), the target angle should temporaraly be change to perpendicular to the moving direction
    for i in range(0, self.frame_per_message):
      if not self.map.is_inside_map(upcoming_frames_position_x[i], upcoming_frames_position_y[i]):
        return True
    return False
  
  #use the binary search to determine the best angle to turn
  def getAngularVelocityRange(self, position_x, position_y, velocity, angle, angle_speed, angle_array):
    angle_size = len(angle_array)
    left_angle_idx = 0
    right_angle_idx = angle_size - 1
    can_be_turn_angle_idx_array = []
    hitting_wall_left_angle = self.hitting_wall_or_not(my_position_x, my_position_y, my_velocity, my_angle + angle_array[left_angle_idx], my_angle_speed)
    hitting_wall_right_angle = self.hitting_wall_or_not(my_position_x, my_position_y, my_velocity, my_angle + angle_array[right_angle_idx] , my_angle_speed)
  
    # as long as one angle will hit the obstacles then find the correct angle range
    # only need to find the right one which fit the situation
    while(hitting_wall_left_angle or hitting_wall_right_angle):
      # if the last one or two idx will hit the wall then left
      if (left_angle_idx + 1 >= right_angle_idx): 
        break
      mid_angle_idx = (left_angle_idx + right_angle)
      mid_angle = angle_array[mid_angle_idx]
      hitting_wall_mid_angle = self.hitting_wall_or_not(position_x, position_y, velocity, angle + mid_angle, angle_speed)
      if hitting_wall_mid_angle:
        right_angle_idx = mid_angle_idx - 1
      else:
        right_angle_idx = mid_angle_idx
    if (not hitting_wall_left_angle and not hitting_wall_right_angle): 
      can_be_turn_angle_idx_array[0] = left_angle_idx
      can_be_turn_angle_idx_array[1] = right_angle_idx
    
    # if not both sides hit the wall then which means there just left one or two angle
    # for one angle, we can just set the left and right to the same value
    # for two angle, since not both sides hit the wall, and the left angle is larger than the right one, so we can just set the left to the right
    # then check if the hitting_wall_left_angle is working
    if (left_angle_idx + 1 >= right_angle_idx and not hitting_wall_left_angle):
         can_be_turn_angle_idx_array[0] = left_angle_idx
         can_be_turn_angle_idx_array[1] = left_angle_idx
    return can_be_turn_angle_idx_array
  
    # otherwise don't set any value

  def update_controller(self):
    # If the gold box exists, set the target to the gold box, else we move to the initial target point
    if self.map.gold_box_exist:
      self.set_target_position(
          self.map.gold_box_position_x, self.map.gold_box_position_y)
    else:
      self.set_target_position(624, 740)

    my_position_x = self.birds.birds[self.team_id].position_x
    my_position_y = self.birds.birds[self.team_id].position_y
    my_velocity_x = self.birds.birds[self.team_id].velocity_x
    my_velocity_y = self.birds.birds[self.team_id].velocity_y
    my_velocity = self.birds.birds[self.team_id].speed
    my_angle = self.birds.birds[self.team_id].angle
    my_angle_speed = self.birds.birds[self.team_id].angularSpeed
    # If the geo distance between my bird and the target is less than 30, get the next position
    if self.map.geo_distance(my_position_x, my_position_y, self.target_x, self.target_y) < 30:
      self.stop_moving()
      return
    # Calculate the angle of the target point to the origin
    target_angle = self.map.calculate_angle(
        self.target_x - my_position_x, self.target_y - my_position_y)
    print("目标角度：" + str(target_angle/3.14))
    moveState = self.birds.birds[self.team_id].moveState
    hitting_wall = self.hitting_wall_or_not(my_position_x, my_position_y, my_velocity, my_angle, my_angle_speed, moveState)
    # Calculate the difference angle between the target angle and my bird's angle
    difference_angle = target_angle - self.birds.birds[self.team_id].angle

    if hitting_wall:
      # self.stop_moving()
      # return
      # creatw an array which fills in angle from -pi to pi which step size is 1/12 pi
      angle_array_left = [math.pi/2, math.pi/3, math.pi/4, math.pi/6, math.pi/12]
      #reverse the down angle array
      angle_array_right=[0, -math.pi/12, -math.pi/6, -math.pi/4, -math.pi/3, -math.pi/2]
      reversed_angle_array_right = angle_array_right[::-1]

      # use binary search to check the angle which will not collide to the obstacles
      leftAngularVelocityRangeIdx = self.getAngularVelocityRange(my_position_x,  my_position_y, my_velocity, my_angle, my_angle_speed, angle_array_left)
      rightAngularVelocityRangeIdx = self.getAngularVelocityRange(my_position_x,  my_position_y, my_velocity, my_angle, my_angle_speed, reversed_angle_array_right)

      # if the left and right angle range is not empty, then we can choose the best angle to turn
      left_angle_exist = True if len(leftAngularVelocityRangeIdx) > 0 else False
      right_angle_exist = True if len(rightAngularVelocityRangeIdx) > 0 else False

      bestAngle = math.pi/2
      if (left_angle_exist and not right_angle_exist):
        bestAngle = angle_array_left[leftAngularVelocityRangeIdx[len(leftAngularVelocityRangeIdx) - 1]]
      elif (right_angle_exist and not left_angle_exist):
        bestAngle = reversed_angle_array_right[rightAngularVelocityRangeIdx[len(rightAngularVelocityRangeIdx) - 1]]
      elif (right_angle_exist and left_angle_exist):
        leftBestAngle = angle_array_left[leftAngularVelocityRangeIdx[len(leftAngularVelocityRangeIdx) - 1]]
        rightBestAngle = reversed_angle_array_right[rightAngularVelocityRangeIdx[len(rightAngularVelocityRangeIdx) - 1]]
        bestAngle = leftBestAngle if(abs(leftBestAngle) < abs(rightBestAngle)) else rightBestAngle
      
      difference_angle = bestAngle
      print("马上要撞了要调整角度！！！！！！！！！")
      print("最佳角度 bestAngle：" + str(bestAngle/3.14))
      # Try to see whether turn the angle -pi/2 will hit the wall
      # hitting_wall_turn_right = self.hitting_wall_or_not(my_position_x, my_position_y, my_velocity, my_angle - math.pi/2, my_angle_speed)
      # # If turning right wont hit the wall, we should turn right
      # if not hitting_wall_turn_right:
      #   difference_angle = self.map.calculate_angle(my_velocity_x, my_velocity_y) - math.pi/2
      # else :
      #   difference_angle = self.map.calculate_angle(my_velocity_x, my_velocity_y) + math.pi/2
      # # If the difference angle is greater than pi, we should minus 2pi
      # if difference_angle > math.pi:
      #   difference_angle = difference_angle - 2 * math.pi
      # # If the difference angle is less than -pi, we should add 2pi
      # elif difference_angle < -math.pi:
      #   difference_angle = difference_angle + 2 * math.pi

    print("角度差：" + str(difference_angle/3.14))

    # If the difference is between -pi/2 to pi/2, move forward otherwise move backward
    # While moving forward, if the turning speed is positive turn right otherwise turn left
    # while moving backward, if the turning speed is positive turn left otherwise turn right
    if difference_angle > -math.pi/2 and difference_angle < math.pi/2:
      self.move_forward()
      # If last time we go backward, we don't want to use the last difference angle
      if self.last_turning_direction != 0:
        last_difference_angle_D = 0
        self.difference_integral = 0
      else:
        last_difference_angle_D = difference_angle - self.last_difference_angle
        self.difference_integral = self.difference_integral + difference_angle
      self.last_turning_direction = 0
      self.last_difference_angle = difference_angle
      factor_P = difference_angle * self.truning_angle_P
      factor_D = last_difference_angle_D * self.truning_angle_D
      factor_I = self.difference_integral * self.turning_angle_I
      truning_speed = factor_P + factor_D + factor_I
      print("P因子：" + str(factor_P))
      print("D因子：" + str(factor_D))
      print("I因子：" + str(factor_I))
      # Make sure the turnning angle is between -0.1 to 0.1
      if truning_speed > 0.1:
        truning_speed = 0.1
      elif truning_speed < -0.1:
        truning_speed = -0.1
      print("转动速度：" + str(truning_speed))
      if truning_speed > 0:
        self.turn_right(truning_speed)
      else:
        self.turn_left(-truning_speed)
    else:
      self.move_backward()
      # While moving backward, the difference_angle is compared against current angle - pi
      difference_angle = difference_angle - math.pi
      # The difference_angle should be between -pi to pi
      if difference_angle < -math.pi:
        difference_angle = difference_angle + 2 * math.pi
      # If last time we go forward, we don't want to use the last difference angle
      if self.last_turning_direction != 1:
        last_difference_angle_D = 0
        self.difference_integral = 0
      else:
        last_difference_angle_D = difference_angle - self.last_difference_angle
        self.difference_integral = self.difference_integral + difference_angle
      self.last_turning_direction = 1
      self.last_difference_angle = difference_angle
      factor_P = difference_angle * self.truning_angle_P
      factor_D = last_difference_angle_D * self.truning_angle_D
      factor_I = self.difference_integral * self.turning_angle_I
      truning_speed = factor_P + factor_D + factor_I
      print("P因子：" + str(factor_P))
      print("D因子：" + str(factor_D))
      print("I因子：" + str(factor_I))
      # Make sure the turnning angle is between -0.1 to 0.1
      if truning_speed > 0.1:
        truning_speed = 0.1
      elif truning_speed < -0.1:
        truning_speed = -0.1
      print("转动速度：" + str(truning_speed))
      if truning_speed > 0:
        self.turn_left(truning_speed)
      else:
        self.turn_right(-truning_speed)
    print("我方菜鸟id: " + self.birds. + "位置：" + str(self.birds.birds[self.team_id].position_x) + "," + str(
        self.birds.birds[self.team_id].position_y))
    
    # # Stop if it is going to hit the wall
    # if hitting_wall:
    #   self.stop_moving()
    #   self.stop_turning()
