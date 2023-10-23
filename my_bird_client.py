#coding=utf-8
import json
import websocket    # pip3 install websocket-client

import map
import cbirds
import controller
import strategy
"""
进入房间的指令
内部参数说明：employeeId为队长工号；roomId为打开游戏主页的管理员工号；accessKey为注册兔子后给的唯一识别码
"""
AI_ENTER_ROOM_COMMAND = {"commandType": "aiEnterRoom", "employeeId": "353395",
                         "roomId": "353395", "accessKey": "1a77644dbfc09a40cc291440a2c9e50a"}


class WebSocketClient(object):

  def __init__(self):
    self.url = 'ws://1024.cainiao.test/ai'      # 这里输入websocket的url
    self.ws = None
    self.my_team_id = "66"
    self.my_map = map.Map()
    self.my_birds = cbirds.CBirds()
    self.my_controller = controller.Controller(self.my_map, self.my_birds, self.my_team_id, self.ws)
    self.my_strategy = strategy.Strategy(self.my_map, self.my_birds, self.my_team_id, self.ws,self.my_controller)

  def on_open(self, ws):
    """
    Callback object which is called at opening websocket.
    1 argument:
    @ ws: the WebSocketApp object
    """
    print('A new webSocketClient is opened!')

    # ai连接房间
    ai_enter_room_str = json.dumps(AI_ENTER_ROOM_COMMAND)
    ws.send(ai_enter_room_str)
    print("ai程序连接房间成功!指令为：", AI_ENTER_ROOM_COMMAND)

  def on_data(self, ws, string, type, continue_flag):
    """
    4 argument.
    The 1st argument is this class object.
    The 2nd argument is utf-8 string which we get from the server.
    The 3rd argument is data type. ABNF.OPCODE_TEXT or ABNF.OPCODE_BINARY will be came.
    The 4th argument is continue flag. If 0, the data continue
    """

  def on_message(self, ws, message):
    self.analyse_and_action(ws, message)

  def on_error(self, ws, error):
    """
    Callback object which is called when got an error.
    2 arguments:
    @ ws: the WebSocketApp object
    @ error: exception object
    """
    print("An error occurs:", error)

  def on_close(self, ws, close_status_code, close_msg):
    """
    Callback object which is called when the connection is closed.
    2 arguments:
    @ ws: the WebSocketApp object
    @ close_status_code
    @ close_msg
    """
    print('The connection is closed!')

  def start(self):
    self.ws = websocket.WebSocketApp(
        self.url,
        on_open=self.on_open,
        on_message=self.on_message,
        on_data=self.on_data,
        on_error=self.on_error,
        on_close=self.on_close,
    )
    self.my_controller.ws = self.ws
    self.ws.run_forever()

  """
    接收大屏指令，分析、作出响应技术策略控制
    """

  def analyse_and_action(self, ws, message):
    data = json.loads(message)
    # 如果接收到开始游戏指令，可以先初始化下地图信息及所有兔子信息
    if data["commandType"] == "startGame":
      print("收到开始游戏指令")
      self.my_map.set_map(data)
      self.my_birds.set_birds(data)
      # Print my team's bird position
      print("我方兔子位置：" + str(self.my_birds.birds[self.my_team_id].position_x) + ", " + str(
          self.my_birds.birds[self.my_team_id].position_y))

    # 如果接收到refreshData指令，会拿到当前游戏中所有兔子状态信息和金萝卜状态信息
    if data["commandType"] == "refreshData":
      # print("收到刷新数据指令")
      self.my_birds.update_birds(data)
      box_exist = self.my_map.update_gold_box(data)
    # 分析后发送行动指令
      self.my_controller.update_controller()
      #self.my_strategy.decision()


if __name__ == "__main__":
  web_socket_client = WebSocketClient()
  web_socket_client.start()
