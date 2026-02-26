import ee

ee.Initialize(project='carbontrust-488607')

point = ee.Geometry.Point([-80.4, 37.2])
print("Earth Engine connected successfully")
print(point.getInfo())