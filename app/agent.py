# app/agent.py

import os
import json
from google import genai
from google.genai import types
import app.config as cfg
from app.carbon import compute_co2e
from app.model import predict_biomass_coefficient

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# --- Tool functions ---

def tool_predict_biomass_coefficient(
    forest_type_code: int,
    canopy_cover_pct: float,
    stand_age: float,
    basal_area_live: float,
) -> dict:
    """
    Predicts the biomass coefficient (tonnes/ha per NDVI unit) for a forest
    using the trained FIA ML model. Call this before estimating carbon.

    Args:
        forest_type_code: FIA forest type code. Use 400 for oak/hardwood,
                         100 for white/red pine, 200 for spruce/fir, 500 for mixed forest.
        canopy_cover_pct: Live canopy cover as a percentage (0-100).
        stand_age: Age of the forest stand in years.
        basal_area_live: Basal area of live trees in sq ft/acre.
    """
    result = predict_biomass_coefficient(
        forest_type_code=forest_type_code,
        canopy_cover_pct=canopy_cover_pct,
        stand_age=stand_age,
        basal_area_live=basal_area_live,
    )
    return {"biomass_coefficient": round(result, 2)}


def tool_estimate_co2e(
    ndvi_change: float,
    area_ha: float,
    biomass_coefficient: float,
) -> dict:
    """
    Estimates CO2e sequestered given an NDVI change, area, and biomass coefficient.
    Always call tool_predict_biomass_coefficient first to get the coefficient.

    Args:
        ndvi_change: Change in NDVI between baseline and monitoring periods.
                    Can be negative for deforestation scenarios.
        area_ha: Project area in hectares.
        biomass_coefficient: Biomass coefficient in tonnes/ha per NDVI unit,
                           obtained from tool_predict_biomass_coefficient.
    """
    original = cfg.BIOMASS_COEFFICIENT
    cfg.BIOMASS_COEFFICIENT = biomass_coefficient
    result = compute_co2e(ndvi_change=ndvi_change, area_ha=area_ha)
    cfg.BIOMASS_COEFFICIENT = original
    return result


# --- Agent ---

def run_agent(user_message: str) -> str:
    print(f"\nUser: {user_message}\n")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction="""You are CarbonTrust, an expert carbon analyst agent.
You help users estimate carbon sequestration for forest projects using satellite data and IPCC methodology.
When given forest parameters, always:
1. First call tool_predict_biomass_coefficient to get a data-driven coefficient from the ML model
2. Then call tool_estimate_co2e with that coefficient
3. Present results clearly with units, methodology notes, and uncertainty ranges
Be concise but precise. Always mention the biomass coefficient used and that it came from a trained ML model.""",
            tools=[tool_predict_biomass_coefficient, tool_estimate_co2e],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=False
            ),
        ),
    )

    print(f"Agent: {response.text}\n")
    return response.text


if __name__ == "__main__":
    run_agent(
        "Analyze a 500 hectare mixed hardwood forest in Virginia. "
        "The forest is 45 years old with 70% canopy cover and basal area of 90 sq ft/acre. "
        "NDVI increased from 0.71 to 0.74 over the monitoring period."
    )