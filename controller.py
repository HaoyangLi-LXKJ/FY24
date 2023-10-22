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
    self.target_y = 730

    self.frame_per_message = 6

    # Last difference angle, used for PD controller
    self.last_difference_angle = 0
    self.last_turning_direction = 0

    self.truning_angle_P = 1/10
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
    print("停止移动")
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

  def update_controller(self):
    # If the gold box exists, set the target to the gold box
    if self.map.gold_box_exist:
      self.set_target_position(
          self.map.gold_box_position_x, self.map.gold_box_position_y)
    my_position_x = self.birds.birds[self.team_id].position_x
    my_position_y = self.birds.birds[self.team_id].position_y
    my_velocity_x = self.birds.birds[self.team_id].velocity_x
    my_velocity_y = self.birds.birds[self.team_id].velocity_y
    # If the geo distance between my bird and the target is less than 5, stop moving
    if self.map.geo_distance(my_position_x, my_position_y, self.target_x, self.target_y) < 20:
      self.stop_moving()
      return
    # Calculate the angle of the target point to the origin
    target_angle = self.map.calculate_angle(
        self.target_x - my_position_x, self.target_y - my_position_y)
    print("目标角度：" + str(target_angle/3.14))
    # Array storing the upcoming frames position
    upcoming_frames_position_x = []
    upcoming_frames_position_y = []
    # Calculate the upcoming frames position
    for i in range(1, self.frame_per_message + 1):
      upcoming_frames_position_x.append(
          my_position_x + my_velocity_x * i)
      upcoming_frames_position_y.append(
          my_position_y + my_velocity_y * i)
    hitting_wall = False
    # If we are going to hit the wall(any of the upcoming frames outside the map), the target angle should temporaraly be change to perpendicular to the moving direction
    for i in range(0, self.frame_per_message):
      if not self.map.is_inside_map(upcoming_frames_position_x[i], upcoming_frames_position_y[i]):
        hitting_wall = True
        print ("将要撞墙")
        print ("撞墙位置：" + str(upcoming_frames_position_x[i]) + "," + str(upcoming_frames_position_y[i]))
        break
    
    if hitting_wall:
      # If we are going to hit the wall, we should set the target to the perpendicular direction
      difference_angle = self.map.calculate_angle(my_velocity_x, my_velocity_y) + math.pi
      # If the difference angle is greater than pi, we should minus 2pi
      if difference_angle > math.pi:
        difference_angle = difference_angle - 2 * math.pi
      # If the difference angle is less than -pi, we should add 2pi
      elif difference_angle < -math.pi:
        difference_angle = difference_angle + 2 * math.pi
    else:
      difference_angle = target_angle - self.birds.birds[self.team_id].angle

    print("角度差：" + str(difference_angle/3.14))

    # If the difference is between -pi/2 to pi/2, move forward otherwise move backward
    # While moving forward, if the turning speed is positive turn right otherwise turn left
    # while moving backward, if the turning speed is positive turn left otherwise turn right
    if difference_angle > -math.pi/2 and difference_angle < math.pi/2:
      self.move_forward()
      # If last time we go backward, we don't want to use the last difference angle
      if self.last_turning_direction != 0:
        last_difference_angle_D = 0
      else:
        last_difference_angle_D = difference_angle - self.last_difference_angle
      self.last_turning_direction = 0
      self.last_difference_angle = difference_angle
      factor_P = difference_angle * self.truning_angle_P
      factor_D = last_difference_angle_D * self.truning_angle_D
      truning_speed = factor_P + factor_D
      print("P因子：" + str(factor_P))
      print("D因子：" + str(factor_D))
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
      else:
        last_difference_angle_D = difference_angle - self.last_difference_angle
      self.last_turning_direction = 1
      self.last_difference_angle = difference_angle
      factor_P = difference_angle * self.truning_angle_P
      factor_D = last_difference_angle_D * self.truning_angle_D
      truning_speed = factor_P + factor_D
      print("P因子：" + str(factor_P))
      print("D因子：" + str(factor_D))
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

    print("我方菜鸟位置：" + str(self.birds.birds[self.team_id].position_x) + "," + str(
        self.birds.birds[self.team_id].position_y))
