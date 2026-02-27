# app/config.py

EE_PROJECT = "carbontrust-488607"

# Sentinel-2 collection
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
CLOUD_THRESHOLD = 20  # max cloud cover %
NDVI_SCALE = 100      # meters per pixel for reduceRegion

# Carbon methodology constants (IPCC 2006 AFOLU Guidelines)
BIOMASS_COEFFICIENT = 53.0   # tonnes/ha per NDVI unit (temperate forest)
CARBON_FRACTION = 0.47       # fraction of biomass that is carbon
CO2_CONVERSION = 3.67        # molecular weight ratio CO2/C
UNCERTAINTY = 0.20           # ±20% uncertainty band

# API metadata
API_TITLE = "CarbonTrust API"
API_DESCRIPTION = "Reproducible satellite-based carbon verification infrastructure"
API_VERSION = "0.1.0"

MONITOR_CRON_HOUR = 6
MONITOR_CRON_MINUTE = 0
NDVI_ANOMALY_THRESHOLD = 0.08
NDVI_FIRE_THRESHOLD = 0.15
NDVI_DEFORESTATION_THRESHOLD = 0.30
MONITOR_LOOKBACK_DAYS = 30
GEMINI_MODEL = "gemini-2.5-flash"