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
my_map.show_map()