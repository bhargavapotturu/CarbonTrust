# app/ndvi.py

import ee
from app.config import EE_PROJECT, S2_COLLECTION, CLOUD_THRESHOLD, NDVI_SCALE


def initialize():
    ee.Initialize(project=EE_PROJECT)


def get_sentinel_image(boundary: ee.Geometry, start_date: str, end_date: str) -> ee.Image:
    """Filter Sentinel-2 collection and return median composite."""
    return (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(boundary)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", CLOUD_THRESHOLD))
        .median()
    )


def compute_ndvi(image: ee.Image) -> ee.Image:
    """Compute NDVI from a Sentinel-2 image using B8 (NIR) and B4 (Red)."""
    return image.normalizedDifference(["B8", "B4"])


def get_mean_ndvi(boundary: ee.Geometry, start_date: str, end_date: str) -> float:
    """
    Full pipeline: fetch imagery, compute NDVI, return mean value for boundary.
    Raises ValueError if no imagery is found for the given date range.
    """
    image = get_sentinel_image(boundary, start_date, end_date)
    ndvi = compute_ndvi(image)

    result = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=boundary,
        scale=NDVI_SCALE
    ).getInfo()

    value = result.get("nd")
    if value is None:
        raise ValueError(
            f"No NDVI data returned for date range {start_date} to {end_date}. "
            "Check your boundary or date range."
        )

    return value