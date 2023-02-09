#this is how to create the json for the front end using random values for the risk assessment

import h3
import json
import random
geoJson = {'type': 'Polygon', 
    'coordinates': [[[-119.880066, 37.561997],
                    [-119.328003, 37.561997],
                    [-119.328003, 38.061067],
                    [-119.880066, 38.061067],
                    [-119.880066, 37.561997]]] }

geojson_out = {
  "type": "FeatureCollection",
  "features": []
}

def json_out():
    for i in hexagons:
        j = random.randint(0,500)/100
        geojson_out["features"].append({
          "type": "Feature",
          "properties": {
              "risk": j
          },
          "geometry": {
            "type": "Polygon",
            "coordinates": [
                h3.h3_to_geo_boundary(i, geo_json=True)
            ]
          }
        })
hexagons = h3.polyfill_geojson(geoJson, 10)
json_out()
hexagons = h3.polyfill_geojson(geoJson, 11)
json_out()
hexagons = h3.polyfill_geojson(geoJson, 12)
json_out()

with open("out.json", "w") as outfile:
    json.dump(geojson_out, outfile)
