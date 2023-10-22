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

    self.target_x = 0
    self.target_y = 0

    # Last turnning angle, used for PD controller
    self.last_angle = 0

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
    self.set_target_position(1000, 600)
    my_position_x = self.birds.birds[self.team_id].position_x
    my_position_y = self.birds.birds[self.team_id].position_y
    my_velocity_x = self.birds.birds[self.team_id].velocity_x
    my_velocity_y = self.birds.birds[self.team_id].velocity_y
    # If the geo distance between my bird and the target is less than 5, stop moving
    if self.map.geo_distance(my_position_x, my_position_y, self.target_x, self.target_y) < 20:
      self.stop_moving()
      return
    # Calculate the angle of the target point to the origin
    target_angle = self.map.calculate_angle(self.target_x - my_position_x, self.target_y - my_position_y)
    print("目标角度：" + str(target_angle/3.14))
    difference_angle = target_angle - self.birds.birds[self.team_id].angle
    print("角度差：" + str(difference_angle/3.14))
    # If the angle difference between the target and my bird is between -pi/2 and pi/2, move forward otherwise move backward
    if -3.14 / 2 < difference_angle < 3.14 / 2:
      self.move_forward()
    else:
      self.move_backward()
    # If the angle difference between the target and my bird is less than 0.02, stop turning
    if abs(difference_angle) < 0.02:
      self.stop_turning()
    # Than, if the difference is between 0 to pi/2 or -pi to -pi/2, turn right otherwise turn left
    elif 0 < difference_angle < 3.14 / 2 or -3.14 < difference_angle < -3.14 / 2:
      self.turn_right(abs(difference_angle) / 20)
    else:
      self.turn_left(abs(difference_angle) / 20)
    print("我方兔子位置：" + str(self.birds.birds[self.team_id].position_x) + "," + str(
        self.birds.birds[self.team_id].position_y))
