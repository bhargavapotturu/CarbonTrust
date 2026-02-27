# tests/test_carbon.py

import pytest
from app.carbon import compute_co2e
from app.config import (
    BIOMASS_COEFFICIENT,
    CARBON_FRACTION,
    CO2_CONVERSION,
    UNCERTAINTY,
)


# --- compute_co2e: pure math, no EE calls needed ---

def test_positive_ndvi_change_produces_positive_co2e():
    result = compute_co2e(ndvi_change=0.05, area_ha=1000)
    assert result["co2e_tonnes"] > 0


def test_negative_ndvi_change_produces_negative_co2e():
    """Deforestation scenario — CO2e should be negative (carbon loss)."""
    result = compute_co2e(ndvi_change=-0.05, area_ha=1000)
    assert result["co2e_tonnes"] < 0


def test_zero_ndvi_change_produces_zero_co2e():
    result = compute_co2e(ndvi_change=0.0, area_ha=1000)
    assert result["co2e_tonnes"] == 0.0


def test_co2e_math_is_correct():
    """Manually verify the pipeline math end to end."""
    ndvi_change = 0.0372
    area_ha = 485492.9

    biomass = ndvi_change * BIOMASS_COEFFICIENT * area_ha
    carbon = biomass * CARBON_FRACTION
    expected_co2e = round(carbon * CO2_CONVERSION, 1)

    result = compute_co2e(ndvi_change=ndvi_change, area_ha=area_ha)
    assert result["co2e_tonnes"] == expected_co2e


def test_uncertainty_bands_are_correct():
    result = compute_co2e(ndvi_change=0.05, area_ha=1000)
    co2e = result["co2e_tonnes"]
    assert result["co2e_low"] == round(co2e * (1 - UNCERTAINTY), 1)
    assert result["co2e_high"] == round(co2e * (1 + UNCERTAINTY), 1)


def test_uncertainty_band_low_less_than_high():
    result = compute_co2e(ndvi_change=0.05, area_ha=1000)
    assert result["co2e_low"] < result["co2e_high"]


def test_larger_area_produces_larger_co2e():
    small = compute_co2e(ndvi_change=0.05, area_ha=100)
    large = compute_co2e(ndvi_change=0.05, area_ha=10000)
    assert large["co2e_tonnes"] > small["co2e_tonnes"]


def test_output_keys_are_complete():
    result = compute_co2e(ndvi_change=0.05, area_ha=1000)
    expected_keys = {
        "biomass_change_tonnes",
        "carbon_sequestered_tonnes_c",
        "co2e_tonnes",
        "co2e_low",
        "co2e_high",
    }
    assert expected_keys == set(result.keys())