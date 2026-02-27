# app/carbon.py

import ee
from app.config import (
    BIOMASS_COEFFICIENT,
    CARBON_FRACTION,
    CO2_CONVERSION,
    UNCERTAINTY,
)
from app.ndvi import get_mean_ndvi


def get_area_ha(boundary: ee.Geometry) -> float:
    """Return the area of a geometry in hectares."""
    return boundary.area().getInfo() / 10000


def estimate_carbon(
    boundary: ee.Geometry,
    baseline_start: str,
    baseline_end: str,
    monitoring_start: str,
    monitoring_end: str,
) -> dict:
    """
    Full carbon estimation pipeline for a given boundary and two time periods.

    Returns a dict with area, NDVI values, biomass, carbon, CO2e, and uncertainty bands.
    """
    area_ha = get_area_ha(boundary)

    baseline_ndvi = get_mean_ndvi(boundary, baseline_start, baseline_end)
    monitoring_ndvi = get_mean_ndvi(boundary, monitoring_start, monitoring_end)
    ndvi_change = monitoring_ndvi - baseline_ndvi

    biomass_change = ndvi_change * BIOMASS_COEFFICIENT * area_ha
    carbon = biomass_change * CARBON_FRACTION
    co2e = carbon * CO2_CONVERSION
    co2e_low = co2e * (1 - UNCERTAINTY)
    co2e_high = co2e * (1 + UNCERTAINTY)

    return {
        "area_ha": round(area_ha, 1),
        "baseline_ndvi": round(baseline_ndvi, 4),
        "monitoring_ndvi": round(monitoring_ndvi, 4),
        "ndvi_change": round(ndvi_change, 4),
        "biomass_change_tonnes": round(biomass_change, 1),
        "carbon_sequestered_tonnes_c": round(carbon, 1),
        "co2e_tonnes": round(co2e, 1),
        "co2e_low": round(co2e_low, 1),
        "co2e_high": round(co2e_high, 1),
    }


def compute_co2e(ndvi_change: float, area_ha: float) -> dict:
    """
    Lightweight version for testing — computes CO2e from known NDVI change
    without making any Earth Engine calls.
    """
    biomass_change = ndvi_change * BIOMASS_COEFFICIENT * area_ha
    carbon = biomass_change * CARBON_FRACTION
    co2e = carbon * CO2_CONVERSION

    return {
        "biomass_change_tonnes": round(biomass_change, 1),
        "carbon_sequestered_tonnes_c": round(carbon, 1),
        "co2e_tonnes": round(co2e, 1),
        "co2e_low": round(co2e * (1 - UNCERTAINTY), 1),
        "co2e_high": round(co2e * (1 + UNCERTAINTY), 1),
    }