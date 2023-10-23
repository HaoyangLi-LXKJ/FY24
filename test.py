import json
import cbirds
import map

#open map.json to test cbirds.py

with open('map.json', 'r') as f:
  data = json.load(f)

my_map = map.Map()
my_map.set_map(data)
# Extract the cainiao from the JSON data
cainiao = data["data"]["cainiao"]
my_birds = cbirds.CBirds()
my_birds.set_birds(data)
# Try to see whether point is inside the map
if my_map.is_inside_map(680, 300):
  print("The point is inside the map")  
  my_map.get_path_intermedia_points(680, 730, 680, 300)
else:
  print("The point is outside the map")
my_map.show_map()