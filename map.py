# Python code to show a map based on the coordinates of the user's location
# and the coordinates of the user's destination
import numpy as np
import networkx as nx
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

    self.grid_resolution = 20  # Adjust the grid resolution as needed
    self.min_x, self.min_y, self.max_x, self.max_y = 0, 0, 0, 0
    self.G = nx.grid_2d_graph(0, 0)

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

    # # Plot each border segment with a different color
    # for segment in borders:
    #   for i, points in enumerate(segment):
    #     color = colors[i % len(colors)]  # Cycle through the list of colors
    #     x_values = [point["x"] for point in points]
    #     y_values = [point["y"] for point in points]
    #     # plt.plot(x_values, y_values, color + '-', linewidth=4)
    #     polygon = Polygon([(x, y) for x, y in zip(x_values, y_values)])
    #     polygons.append(polygon)

    # Create polygons for the blocks and append them to the list
    # And show the block coords in the map
    # Broden the block polygon by 47.5 to make sure the bird won't hit the block
    for block in blocks:
      block_coords = [(point["x"], point["y"]) for point in block[0]]
      block_polygon = Polygon(block_coords)
      block_polygon = block_polygon.buffer(60)
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
      block_polygon = block_polygon.buffer(60)
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

    # Define grid parameters
    grid_width = int(width / self.grid_resolution)
    grid_height = int(height / self.grid_resolution)

    # Create a grid representation of the map
    grid = np.zeros((grid_width, grid_height), dtype=bool)

    # Create a graph based on the grid
    self.G = nx.grid_2d_graph(grid_width, grid_height)

    # Mark grid cells inside the combined polygon as obstacles
    for x in range(grid_width):
        for y in range(grid_height):
            cell_x = x * self.grid_resolution
            cell_y = y * self.grid_resolution
            point = Point(cell_x, cell_y)
            if self.prohibited_polygons.contains(point):
              self.G.remove_node((x, y))

  def is_inside_map(self, x, y):
    # Try to see whether x, y is in the graph G
    # Find the grid cell indices
    x_index = int((x - self.min_x) / self.grid_resolution)
    y_index = int((y - self.min_y) / self.grid_resolution)
    # If the grid cell indices are not in the graph G, return False
    return self.G.has_node((x_index, y_index))

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

  # Define a Manhattan distance heuristic
  def manhattan_distance(self, node1, node2):
      x1, y1 = node1
      x2, y2 = node2
      return abs(x1 - x2) + abs(y1 - y2)

  def get_path_intermedia_points(self, start_x, start_y, target_x, target_y):
    # Get an intermediate path from point start to point target without getting into the combined_polygon
    # Find the start and target grid cell indices
    start = (int((start_x - self.min_x) / self.grid_resolution), int((start_y - self.min_y) / self.grid_resolution))
    target = (int((target_x - self.min_x) / self.grid_resolution), int((target_y - self.min_y) / self.grid_resolution))

    # Check whether the start is in the graph G, if not add/minus the start by 1 until it is in the graph G, if it is still not in the graph G, return the start point
    i = 0
    j = 0
    while not self.G.has_node(start):
      i += 1
      j += 1
      if i % 4 == 0:
        start = (start[0] + j, start[1])
      elif i % 4 == 1:
        start = (start[0] - j, start[1])
      elif i % 4 == 2:
        start = (start[0], start[1] + j)
      elif i % 4 == 3:
        start = (start[0], start[1] - j)
      elif j > 3:
        print("Start is not in the graph G")
        # Return the list of start point
        return [[start_x], [start_y]]
    #Before finding the path, check whether the target is in the graph G, if not add/minus the target by 1 until it is in the graph G, if it is still not in the graph G, return the start point
    i = 0
    j = 0
    while not self.G.has_node(target):
      i += 1
      j += 1
      if i % 4 == 0:
        target = (target[0] + j, target[1])
      elif i % 4 == 1:
        target = (target[0] - j, target[1])
      elif i % 4 == 2:
        target = (target[0], target[1] + j)
      elif i % 4 == 3:
        target = (target[0], target[1] - j)
      elif j > 3:
        print("Target is not in the graph G")
        # Return the list of start point
        return [[start_x], [start_y]]
    # Find a path using A* algorithm while avoiding obstacles
    path = nx.astar_path(self.G, start, target, heuristic=self.manhattan_distance, weight='weight')

    # Convert grid cell indices back to coordinates
    intermediate_path = [(x * self.grid_resolution + self.min_x, y * self.grid_resolution + self.min_y) for x, y in path]

    self.ax.plot(*zip(*intermediate_path), marker='o', markersize=4, linestyle='-')
    self.ax.plot(start_x, start_y, 'go', markersize=8, label='Start')
    self.ax.plot(target_x, target_y, 'bo', markersize=8, label='Target')
    # Return the list of intermediate points
    return [list(a) for a in zip(*intermediate_path)]

    
