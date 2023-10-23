import time
import math

# 预设线路
line_points = [
  {"x": 876, "y": 566},
  {"x": 942, "y": 368},
  {"x": 714, "y": 191},
  {"x": 568, "y": 327},
  {"x": 601, "y": 412},
  {"x": 723, "y": 400},
  {"x": 815, "y": 454},
]

size = len(line_points)

def last_point_index(i):
  return (i + size - 1) % size

def next_point_index(i):
  return (i + size + 1) % size

# 两点之间的距离
def distance(x1, y1, x2, y2):
  return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

# 判断当前点是否在线段上
def if_in_line(x1, y1, x2, y2, curr_x, curr_y):
  d1 = distance(x1, y1, curr_x, curr_y)
  d2 = distance(x2, y2, curr_x, curr_y)
  print("dist"+str(abs(d1 + d2 - distance(x1, y1, x2, y2))))
  return abs(d1 + d2 - distance(x1, y1, x2, y2)) <= 50

# 判断是否在上次预设目标的路途之中
def is_in_line(next_i, curr_x, curr_y):
  last_i = last_point_index(next_i)
  p1 = line_points[last_i]
  x1, y1 = p1["x"], p1["y"]
  p2 = line_points[next_i]
  x2, y2 = p2["x"], p2["y"]
  if if_in_line(x1, y1, x2, y2, curr_x, curr_y):
    d = distance(x2, y2, curr_x, curr_y)
    print("d:"+str(d))
    if d<50 :
      next_i = next_point_index(next_i)
    return next_i
  else:
    return -1

class Strategy:
  def __init__(self, map, birds, team_id, ws, control):
    self.map = map
    self.birds = birds
    self.team_id = team_id
    self.ws = ws

    self.next_index = 0

    self.target_x = 0
    self.target_y = 0
    self.control = control

  def decision(self):
    self.debug("decision")
    now = int(time.time())
    if self.map.gold_box_exist:
      self.targetGoldPackage()
    elif self.birds.birds[self.team_id].invincible:
      self.attack()
    else:
      diff = now-self.map.starttime
      if diff % 30<15:
        self.runAround()
      else:
        self.runAround()

  #绕石头跑
  def runAround(self):
    print("start runAround")
    self.curr_x = self.birds.birds[self.team_id].position_x
    self.curr_y = self.birds.birds[self.team_id].position_y
    # 如果现在还跑在上次预设目标的路线上，继续跑
    self.next_index = is_in_line(self.next_index, self.curr_x, self.curr_y)
    if self.next_index>=0:
      self.control.set_target_position(line_points[self.next_index]["x"],line_points[self.next_index]["y"])
      self.control.update_controller()
    else :
      # 否则判断当前离哪个点最近，并设置为目标值
      self.cal_and_set_most_recent_point_target()

  #拿到金包裹主动攻击
  def attack(self):
    self.debug("attack")
    max = 0
    maxp = -1
    for (k,v) in self.birds.birds.items():
      if v.score>max and k != self.team_id:
        max = v.score
        maxp = k
    if maxp != -1:
      self.control.forward_to_target_team(maxp)
    else:
      self.runAround()

  #抢金包裹
  def targetGoldPackage(self):
    self.control.set_target_position(self.map.gold_box_position_x,self.map.gold_box_position_y)
    self.control.update_controller()
    print("抢金包裹")

  # 计算并设置离预设线路最近的点
  def cal_and_set_most_recent_point_target(self):
    min_distance = 0x100000000
    for i in range(size):
      p = line_points[i];
      x, y = p["x"], p["y"]
      if distance(x, y, self.curr_x, self.curr_y) < min_distance:
        self.next_index = i
        self.target_x = x
        self.target_y = y
        min_distance = distance(x, y, self.curr_x, self.curr_y)
    self.control.set_target_position(self.target_x,self.target_y)
    self.control.update_controller()
  def debug(self,v):
    print(v)
