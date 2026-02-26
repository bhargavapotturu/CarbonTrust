import ee
import matplotlib.pyplot as plt
import numpy as np

# Connect to Earth Engine
ee.Initialize(project='carbontrust-488607')

# Define a forest area in Virginia (George Washington National Forest)
boundary = ee.Geometry.Rectangle([-79.5, 38.0, -78.5, 38.5])

# Load Sentinel-2 imagery and filter it
def get_sentinel_image(start_date, end_date):
    return (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(boundary)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            .median())

# Compute NDVI from an image
def compute_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4'])
    return ndvi

# Get baseline and monitoring images
baseline_image = get_sentinel_image('2021-06-01', '2021-09-01')
monitoring_image = get_sentinel_image('2023-06-01', '2023-09-01')

# Compute NDVI for both periods
baseline_ndvi = compute_ndvi(baseline_image)
monitoring_ndvi = compute_ndvi(monitoring_image)

# Get mean NDVI values for the area
baseline_mean = baseline_ndvi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=boundary,
    scale=100
).getInfo()

monitoring_mean = monitoring_ndvi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=boundary,
    scale=100
).getInfo()

print(f"Baseline NDVI (2021): {baseline_mean['nd']:.4f}")
print(f"Monitoring NDVI (2023): {monitoring_mean['nd']:.4f}")
print(f"NDVI Change: {monitoring_mean['nd'] - baseline_mean['nd']:.4f}")