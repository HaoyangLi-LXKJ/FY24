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

    self.arrive_distance = 40
    self.target_x = 0
    self.target_y = 0
    # Fifo storing all the intermediate target points
    self.target_points_x = []
    self.target_points_y = []

    self.frame_per_message = 6

    # Last difference angle, used for PD controller
    self.last_difference_angle = 0
    self.last_turning_direction = 0
    self.difference_integral = 0

    self.truning_angle_P = 0.17
    self.turning_angle_I = 0.01
    self.truning_angle_D = 0.14

  def move_forward(self):
    # print("向前移动")
    self.ws.send(json.dumps({"commandType": "goForward"}))

  def move_backward(self):
    # print("向后移动")
    self.ws.send(json.dumps({"commandType": "goBack"}))

  def turn_left(self, speed):
    # print("向左转动")
    self.ws.send(json.dumps({"commandType": "turnLeft", "data": speed}))

  def turn_right(self, speed):
    # print("向右转动")
    self.ws.send(json.dumps({"commandType": "turnRight", "data": speed}))

  def stop_turning(self):
    # print("停止转动")
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
    # If the positions are the same, return
    if self.target_x == x and self.target_y == y:
      return
    self.target_x = x
    self.target_y = y
    # Get the intermediate target x and y from the map
    self.target_points_x, self.target_points_y = self.map.get_path_intermedia_points(
        self.birds.birds[self.team_id].position_x, self.birds.birds[self.team_id].position_y, x, y)
    # Take only 3 intermediate target points, first, last and the middle in with the same distance to each other
    if len(self.target_points_x) >= 4:
      len_of_target_points = len(self.target_points_x)
      self.target_points_x = [self.target_points_x[0], self.target_points_x[int(len_of_target_points/3)],
                              self.target_points_x[int(len_of_target_points / 3 * 2)], self.target_points_x[-1]]
      self.target_points_y = [self.target_points_y[0],
                              self.target_points_y[int(len_of_target_points/3)], self.target_points_y[int(len_of_target_points/3 * 2)], self.target_points_y[-1]]
    # self.target_points_x = [self.target_points_x[-1]]
    # self.target_points_y = [self.target_points_y[-1]]

  def update_controller(self):
    # If the gold box exists, set the target to the gold box, else we move to the initial target point
    if self.map.gold_box_exist:
      self.set_target_position(self.map.gold_box_position_x, self.map.gold_box_position_y)
    elif self.birds.get_past_time_in_ms() < 10000:
      self.set_target_position(680, 730)
    else:
      self.set_target_position(680, 300)

    my_position_x = self.birds.birds[self.team_id].position_x
    my_position_y = self.birds.birds[self.team_id].position_y
    my_velocity_x = self.birds.birds[self.team_id].velocity_x
    my_velocity_y = self.birds.birds[self.team_id].velocity_y
    my_velocity = self.birds.birds[self.team_id].speed
    my_angle = self.birds.birds[self.team_id].angle
    my_angle_speed = self.birds.birds[self.team_id].angularSpeed
    my_moveState = self.birds.birds[self.team_id].moveState
    # Set the tempo target x and tempo target y to the first intermediate target point, if there is no intermediate target point, set the target x and target y to the my position x and my position y
    if len(self.target_points_x) > 0:
      tempo_target_x = self.target_points_x[0]
      tempo_target_y = self.target_points_y[0]
    else:
      self.stop_moving()
      return

    # If the geo distance between my bird and the target is less than 5, stop moving
    while self.map.geo_distance(my_position_x, my_position_y, tempo_target_x, tempo_target_y) < self.arrive_distance:
      # If we are moving to tempo target, remove the tempo target from the target points
      if len(self.target_points_x) > 0:
        self.target_points_x.pop(0)
        self.target_points_y.pop(0)
      # Try to set the tempo target to the next intermediate target point, if there is no intermediate target point, set the target x and target y to the my position x and my position y
      if len(self.target_points_x) > 0:
        tempo_target_x = self.target_points_x[0]
        tempo_target_y = self.target_points_y[0]
      else:
        self.stop_moving()
        return
    # Calculate the angle of the target point to the origin
    target_angle = self.map.calculate_angle(
        tempo_target_x - my_position_x, tempo_target_y - my_position_y)
    # print("目标角度：" + str(target_angle/3.14))
    # Calculate the difference angle between the target angle and my bird's angle
    difference_angle = target_angle - self.birds.birds[self.team_id].angle
    # If the difference angle is less than -pi, add 2pi to it
    if difference_angle < -math.pi:
      difference_angle = difference_angle + 2 * math.pi
    # If the difference angle is greater than pi, subtract 2pi from it
    if difference_angle > math.pi:
      difference_angle = difference_angle - 2 * math.pi
    # print("角度差：" + str(difference_angle/3.14))

    # If the difference is between -pi/2 to pi/2, move forward otherwise move backward
    # While moving forward, if the turning speed is positive turn right otherwise turn left
    # while moving backward, if the turning speed is positive turn left otherwise turn right
    if difference_angle > -math.pi/2 and difference_angle < math.pi/2:
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
      # print("P因子：" + str(factor_P))
      # print("D因子：" + str(factor_D))
      # print("I因子：" + str(factor_I))
      # Make sure the turnning angle is between -0.1 to 0.1
      if truning_speed > 0.1:
        truning_speed = 0.1
      elif truning_speed < -0.1:
        truning_speed = -0.1
      # print("转动速度：" + str(truning_speed))
      if truning_speed > 0:
        self.turn_right(truning_speed)
      else:
        self.turn_left(-truning_speed)
      self.move_forward()
    else:
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
      # print("P因子：" + str(factor_P))
      # print("D因子：" + str(factor_D))
      # print("I因子：" + str(factor_I))
      # Make sure the turnning angle is between -0.1 to 0.1
      if truning_speed >= 0.1:
        truning_speed = 0.1
      elif truning_speed <= -0.1:
        truning_speed = -0.1
      # print("转动速度：" + str(truning_speed))
      if truning_speed >= 0.01:
        self.turn_left(truning_speed)
      elif truning_speed <= -0.01:
        self.turn_right(-truning_speed)
      else:
        self.stop_turning()
      self.move_backward()
    # print("我方菜鸟位置：" + str(self.birds.birds[self.team_id].position_x) + "," + str(
    #     self.birds.birds[self.team_id].position_y))

    # # Stop if it is going to hit the wall
    # if hitting_wall:
    #   self.stop_moving()
    #   self.stop_turning()
