# Python code to show a map based on the coordinates of the user's location
# and the coordinates of the user's destination
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from matplotlib.patches import Polygon as MatplotlibPolygon
from random import random
import math
import json
# define the map hanlding class


class Map:
  def __init__(self):
    self.prohibited_polygons = MultiPolygon()
    self.battle_polygons = Rectangle((0, 0), 0, 0)
    self.gold_box_position_x = 0
    self.gold_box_position_y = 0
    self.gold_box_exist = False

    # Create a figure and axis for the map
    self.fig, self.ax = plt.subplots()  # Adjust the scaling factor as needed
  def set_map(self, data):
    # Save the data in map.json
    with open('map.json', 'w') as f:
      json.dump(data, f)
    # Extract the width and height from the JSON data
    width = data["data"]["map"]["width"]
    height = data["data"]["map"]["height"]

    # Extract the border and the blocks coordinates of the map
    borders = data["data"]["map"]["borders"]
    blocks = data["data"]["map"]["blocks"]

    # Create a list of colors for the border segments
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    # Create a list to store the border segments as Polygon objects
    polygons = []

    # Plot each border segment with a different color
    for segment in borders:
      for i, points in enumerate(segment):
        color = colors[i % len(colors)]  # Cycle through the list of colors
        x_values = [point["x"] for point in points]
        y_values = [point["y"] for point in points]
        # plt.plot(x_values, y_values, color + '-', linewidth=4)
        polygon = Polygon([(x, y) for x, y in zip(x_values, y_values)])
        polygons.append(polygon)

    # Create polygons for the blocks and append them to the list
    # And show the block coords in the map
    for block in blocks:
      block_coords = [(point["x"], point["y"]) for point in block[0]]
      block_polygon = Polygon(block_coords)
      polygons.append(block_polygon)
      # Show the block coords in the map
      x_values = [point["x"] for point in block[0]]
      y_values = [point["y"] for point in block[0]]
      plt.plot(x_values, y_values, 'k-', linewidth=4)

      # Create polygons for the blocks in block[1] and append them to the list
    # And show the block coords in the map with different color
    for block in blocks:
      block_coords = [(point["x"], point["y"]) for point in block[1]]
      block_polygon = Polygon(block_coords)
      polygons.append(block_polygon)
      # Show the block coords in the map
      x_values = [point["x"] for point in block[1]]
      y_values = [point["y"] for point in block[1]]
      plt.plot(x_values, y_values, 'r-', linewidth=4)

    # Create a rectangle to represent the width and height
    self.battle_polygons = Rectangle((0, 0), width, height, fill=False,
                                     color='k', linestyle='--', linewidth=2)
    self.ax.add_patch(self.battle_polygons)

    # Combine all the individual polygons into one
    self.prohibited_polygons = unary_union(polygons)

    # Plot the combined polygon
    for polygon in self.prohibited_polygons.geoms:
      x, y = polygon.exterior.xy
      polygon_patch = MatplotlibPolygon(
          list(zip(x, y)), fill=False, edgecolor='k', linewidth=2)
      self.ax.fill(x, y, alpha=0.5, color='red', linewidth=2)

    # Set map title and labels
    self.ax.set_title('Map of the world')
    self.ax.set_xlabel('X')
    self.ax.set_ylabel('Y')

  def is_inside_map(self, x, y):
    point = Point(x, y)
    if not self.battle_polygons.contains(point):
      return False
    return self.prohibited_polygons.contains(point)

  def update_gold_box(self, data):
    # If the gold box doesn't have x, and y coordinates, return False
    if "x" not in data["data"]["goldBox"] or "y" not in data["data"]["goldBox"]:
      self.gold_box_exist = False
      return
    self.gold_box_position_x = data["data"]["goldBox"]["x"]
    self.gold_box_position_y = data["data"]["goldBox"]["y"]
    print("金箱子位置：" + str(self.gold_box_position_x) +
          "," + str(self.gold_box_position_y))
    self.gold_box_exist = True

  def geo_distance(self, x1, y1, x2, y2):
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5
  
  def calculate_angle(self, x, y):
    return math.atan2(y, x)

  def show_map(self):
    plt.show()