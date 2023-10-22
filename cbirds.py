import json

class CBird:
  def __init__(self):
    self.id = 0
    self.name = ""
    self.score = 0
    self.active = True
    self.energy = 1000
    self.invincible = False
    self.moveState = 0
    self.dirState = 0
    self.velocity_x = 0
    self.velocity_y = 0
    self.position_x = 0
    self.position_y = 0
    self.angle = 0
    self.angularSpeed = 0
    self.rebounding = False
    self.reboundAngle = 0
    self.attacking = False
    self.deathCount = 0
    self.position_history_x = []
    self.position_history_y = []

# Define the class for holding all the birds in an id mapped dictionary


class CBirds:
  def __init__(self):
    self.birds = dict()
    self.lastTimeStamp = 0
    self.timeStamp = 0

  def set_birds(self, data):
    # Extract the birds data from the JSON data
    birds_data = data["data"]["cainiao"]

    # Create a dictionary to store the birds
    self.birds.clear()

    # Loop through the birds data
    for bird in birds_data:
      # Create a new bird object
      cbird = CBird()

      # Extract the bird data
      cbird.id = bird["id"]
      cbird.name = bird["name"]
      cbird.score = bird["score"]
      cbird.active = bird["active"]
      cbird.energy = bird["energy"]
      cbird.invincible = bird["invincible"]
      cbird.moveState = bird["moveState"]
      cbird.dirState = bird["dirState"]
      cbird.velocity_x = bird["velocity"]["x"]
      cbird.velocity_y = bird["velocity"]["y"]
      cbird.speed = bird["speed"]
      cbird.position_x = bird["position"]["x"]
      cbird.position_y = bird["position"]["y"]
      cbird.angle = bird["angle"]
      cbird.angularSpeed = bird["angularSpeed"]
      cbird.rebounding = bird["rebounding"]
      cbird.reboundAngle = bird["reboundAngle"]
      cbird.attacking = bird["attacking"]
      cbird.deathCount = bird["deathCount"]

      # Add the bird to the dictionary with name as key
      self.birds[cbird.id] = cbird
    self.timeStamp = data["timeStamp"]

  # Update the birds data based on id in data
  def update_birds(self, data):
    # Extract the birds data from the JSON data
    birds = data["data"]["cainiao"]

    # Loop through the birds data
    for bird in birds:
      # Get the bird object from the dictionary
      cbird = self.birds[bird["id"]]

      # Extract the bird data
      cbird.id = bird["id"]
      cbird.name = bird["name"]
      cbird.score = bird["score"]
      cbird.active = bird["active"]
      cbird.energy = bird["energy"]
      cbird.invincible = bird["invincible"]
      cbird.moveState = bird["moveState"]
      cbird.dirState = bird["dirState"]
      cbird.velocity_x = bird["velocity"]["x"]
      cbird.velocity_y = bird["velocity"]["y"]
      cbird.speed = bird["speed"]
      cbird.position_x = bird["position"]["x"]
      cbird.position_y = bird["position"]["y"]
      cbird.angle = bird["angle"]
      cbird.angularSpeed = bird["angularSpeed"]
      cbird.rebounding = bird["rebounding"]
      cbird.reboundAngle = bird["reboundAngle"]
      cbird.attacking = bird["attacking"]
      cbird.deathCount = bird["deathCount"]
      cbird.position_history_x.append(bird["position"]["x"])
      cbird.position_history_y.append(bird["position"]["y"])

    self.lastTimeStamp = self.timeStamp
    self.timeStamp = data["timeStamp"]

  def get_bird(self, id):
    return self.birds[id]
