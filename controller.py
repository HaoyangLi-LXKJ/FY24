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
    self.difference_integral = 0

    self.truning_angle_P = 1/12
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

  def hitting_wall_or_not(self, position_x, position_y, velocity, angle, angle_speed, moveState):
    # Array storing the upcoming frames position
    upcoming_frames_position_x = []
    upcoming_frames_position_y = []
    # If the moveState is -1, it is moving backward, the angle is the opposite direction
    if moveState == -1:
      angle = angle - math.pi
    # Calculate the current frame position
    upcoming_frames_position_x.append(position_x + velocity * math.cos(angle))
    upcoming_frames_position_y.append(position_y + velocity * math.sin(angle))
    # Calculate the upcoming frames position
    for i in range(1, self.frame_per_message):
      upcoming_frames_position_x.append(
          upcoming_frames_position_x[i-1] + velocity * math.cos(angle + angle_speed * i))
      upcoming_frames_position_y.append(
          upcoming_frames_position_y[i-1] + velocity * math.sin(angle + angle_speed * i))
    # If we are going to hit the wall(any of the upcoming frames outside the map), the target angle should temporaraly be change to perpendicular to the moving direction
    for i in range(0, self.frame_per_message):
      if not self.map.is_inside_map(upcoming_frames_position_x[i], upcoming_frames_position_y[i]):
        return True
    return False

  def update_controller(self):
    # If the gold box exists, set the target to the gold box, else we move to the initial target point
    if self.map.gold_box_exist:
      self.set_target_position(self.map.gold_box_position_x, self.map.gold_box_position_y)
    elif self.birds.get_past_time_in_ms() < 5000:
      self.set_target_position(680, 730)
    else: 
      self.set_target_position(680, 200)

    my_position_x = self.birds.birds[self.team_id].position_x
    my_position_y = self.birds.birds[self.team_id].position_y
    my_velocity_x = self.birds.birds[self.team_id].velocity_x
    my_velocity_y = self.birds.birds[self.team_id].velocity_y
    my_velocity = self.birds.birds[self.team_id].speed
    my_angle = self.birds.birds[self.team_id].angle
    my_angle_speed = self.birds.birds[self.team_id].angularSpeed
    my_moveState = self.birds.birds[self.team_id].moveState
    # If the geo distance between my bird and the target is less than 5, stop moving
    if self.map.geo_distance(my_position_x, my_position_y, self.target_x, self.target_y) < 30:
      self.stop_moving()
      return
    # Calculate the angle of the target point to the origin
    target_angle = self.map.calculate_angle(
        self.target_x - my_position_x, self.target_y - my_position_y)
    print("目标角度：" + str(target_angle/3.14))
    hitting_wall = self.hitting_wall_or_not(my_position_x, my_position_y, my_velocity, my_angle, my_angle_speed, my_moveState)
    # Calculate the difference angle between the target angle and my bird's angle
    difference_angle = target_angle - self.birds.birds[self.team_id].angle
    
    if hitting_wall:
      # self.stop_moving()
      # return
      # If the bird is moving backward, the angle should be the opposite direction
      if my_moveState == -1:
        angle_temp = my_angle - math.pi
      else:
        angle_temp = my_angle
      # Try to see whether turn the angle -pi/2 will hit the wall
      angle_try_right = angle_temp - math.pi/2
      # If the angle is less than -pi, we should add 2pi
      if angle_try_right < -math.pi:
        angle_try_right = angle_try_right + 2 * math.pi
      # If the trying right angle is between -pi/2 to pi/2, we move forward, otherwise we move backward
      moving_forward = -1
      if angle_try_right > -math.pi/2 and angle_try_right < math.pi/2:
        moving_forward = 1
      hitting_wall_turn_right = self.hitting_wall_or_not(my_position_x, my_position_y, my_velocity, angle_try_right, moving_forward)
      # If turning right wont hit the wall, we should turn right
      if not hitting_wall_turn_right:
        difference_angle = - math.pi / 7 * 2
      else :
        difference_angle = math.pi / 7 * 2
      # If the difference angle is greater than pi, we should minus 2pi
      if difference_angle > math.pi:
        difference_angle = difference_angle - 2 * math.pi
      # If the difference angle is less than -pi, we should add 2pi
      elif difference_angle < -math.pi:
        difference_angle = difference_angle + 2 * math.pi

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
      if truning_speed >= 0.1:
        truning_speed = 0.1
      elif truning_speed <= -0.1:
        truning_speed = -0.1
      print("转动速度：" + str(truning_speed))
      if truning_speed >= 0.01:
        self.turn_left(truning_speed)
      elif truning_speed <= -0.01:
        self.turn_right(-truning_speed)
      else:
        self.stop_turning()
    print("我方菜鸟位置：" + str(self.birds.birds[self.team_id].position_x) + "," + str(
        self.birds.birds[self.team_id].position_y))
    
    # # Stop if it is going to hit the wall
    # if hitting_wall:
    #   self.stop_moving()
    #   self.stop_turning()
