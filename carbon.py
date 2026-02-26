import ee

# Connect to Earth Engine
ee.Initialize(project='carbontrust-488607')

# --- Constants (from published literature / IPCC guidelines) ---
BIOMASS_SCALING_COEFFICIENT = 53.0  # tonnes/ha per NDVI unit (temperate forest)
CARBON_FRACTION = 0.47              # IPCC 2006 guidelines
CO2_CONVERSION = 3.67               # molecular weight ratio CO2/C
UNCERTAINTY = 0.20                  # ±20% uncertainty band

# --- Project area ---
boundary = ee.Geometry.Rectangle([-79.5, 38.0, -78.5, 38.5])

# --- Area calculation ---
area_m2 = boundary.area().getInfo()
area_ha = area_m2 / 10000
print(f"Project area: {area_ha:,.1f} hectares")

# --- NDVI values from our previous script ---
baseline_ndvi = 0.7265
monitoring_ndvi = 0.7637
ndvi_change = monitoring_ndvi - baseline_ndvi
print(f"NDVI Change: {ndvi_change:.4f}")

# --- Biomass change estimation ---
biomass_change = ndvi_change * BIOMASS_SCALING_COEFFICIENT * area_ha
print(f"Biomass Change: {biomass_change:,.1f} tonnes")

# --- Carbon estimation ---
carbon = biomass_change * CARBON_FRACTION
print(f"Carbon Sequestered: {carbon:,.1f} tonnes C")

# --- CO2e conversion ---
co2e = carbon * CO2_CONVERSION
print(f"CO2e Sequestered: {co2e:,.1f} tonnes CO2e")

# --- Uncertainty bands ---
co2e_low = co2e * (1 - UNCERTAINTY)
co2e_high = co2e * (1 + UNCERTAINTY)
print(f"Uncertainty Range: {co2e_low:,.1f} - {co2e_high:,.1f} tonnes CO2e (±{UNCERTAINTY*100:.0f}%)")

# --- Summary ---
print("\n--- CARBON ESTIMATION SUMMARY ---")
print(f"Project Area:        {area_ha:,.1f} ha")
print(f"Baseline NDVI:       {baseline_ndvi:.4f}")
print(f"Monitoring NDVI:     {monitoring_ndvi:.4f}")
print(f"NDVI Change:         {ndvi_change:.4f}")
print(f"Biomass Change:      {biomass_change:,.1f} t")
print(f"Carbon Sequestered:  {carbon:,.1f} t C")
print(f"CO2e Sequestered:    {co2e:,.1f} t CO2e")
print(f"Uncertainty Range:   {co2e_low:,.1f} - {co2e_high:,.1f} t CO2e")
print(f"Methodology:         IPCC 2006 AFOLU Guidelines")
print(f"Satellite Data:      Sentinel-2 SR Harmonized")