// src/components/ResultsPanel.jsx
import { useState, useEffect } from "react"
import axios from "axios"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts"

const API_BASE = "http://localhost:8000"

function MetricCard({ label, value, unit, highlight }) {
  if (highlight) {
    return (
      <div className="col-span-2 rounded-xl p-5 gradient-carbon shadow-lg shadow-forest-950/50">
        <p className="text-xs font-semibold uppercase tracking-wide text-forest-200 mb-1">
          {label}
        </p>
        <p className="text-4xl font-bold text-white">
          {typeof value === "number" ? value.toLocaleString() : value}
        </p>
        <p className="text-sm text-forest-300 mt-1">{unit}</p>
      </div>
    )
  }
  return (
    <div className="glass rounded-xl p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-forest-300 mb-1">
        {label}
      </p>
      <p className="text-xl font-bold text-white">
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      <p className="text-xs text-forest-300 mt-0.5">{unit}</p>
    </div>
  )
}

function HashBadge({ hash }) {
  return (
    <div className="glass-dark rounded-xl p-4">
      <p className="text-xs font-semibold text-forest-300 uppercase tracking-wide mb-1">
        SHA-256 Run Hash
      </p>
      <p className="text-xs font-mono text-forest-200 break-all">{hash}</p>
    </div>
  )
}

function AIInterpretation({ results, formParams }) {
  const [interpretation, setInterpretation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchInterpretation = async () => {
      setLoading(true)
      setError(null)
      try {
        const payload = {
          project_name: results.project_name,
          area_ha: results.area_ha,
          baseline_ndvi: results.baseline_ndvi,
          monitoring_ndvi: results.monitoring_ndvi,
          ndvi_change: results.ndvi_change,
          biomass_change_tonnes: results.biomass_change_tonnes,
          carbon_sequestered_tonnes_c: results.carbon_sequestered_tonnes_c,
          co2e_tonnes: results.co2e_tonnes,
          co2e_low: results.co2e_low,
          co2e_high: results.co2e_high,
          uncertainty_pct: results.uncertainty_pct,
          forest_type_code: formParams.forest_type_code,
          canopy_cover_pct: formParams.canopy_cover_pct,
          stand_age: formParams.stand_age,
          basal_area_live: formParams.basal_area_live,
          baseline_start: formParams.baseline_start,
          baseline_end: formParams.baseline_end,
          monitoring_start: formParams.monitoring_start,
          monitoring_end: formParams.monitoring_end,
        }
        const { data } = await axios.post(`${API_BASE}/interpret`, payload)
        setInterpretation(data.interpretation)
      } catch (err) {
        setError("AI interpretation unavailable.")
      } finally {
        setLoading(false)
      }
    }

    fetchInterpretation()
  }, [results.run_hash])

  return (
    <div className="glass rounded-2xl p-6 border border-blue-500/10">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 rounded-md bg-blue-500/20 flex items-center justify-center flex-shrink-0">
          <span className="text-blue-400 text-xs font-bold">AI</span>
        </div>
        <h3 className="text-sm font-bold text-white">AI Interpretation</h3>
        <span className="text-xs glass text-blue-400 px-2 py-0.5 rounded-full ml-auto border border-blue-500/20">
          Gemini 2.5 Flash
        </span>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-forest-300 py-4">
          <div className="w-5 h-5 border-2 border-forest-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
          <p className="text-sm">Analyzing your forest data...</p>
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      {interpretation && !loading && (
        <div className="space-y-3">
          {interpretation.split("\n\n").filter(p => p.trim()).map((paragraph, i) => (
            <p key={i} className="text-sm text-forest-300 leading-relaxed">
              {paragraph.trim()}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ResultsPanel({ results, formParams }) {
  const chartData = [
    { name: "Low (−20%)",  co2e: results.co2e_low,    fill: "#12401f" },
    { name: "Estimate",    co2e: results.co2e_tonnes,  fill: "#2d8653" },
    { name: "High (+20%)", co2e: results.co2e_high,    fill: "#12401f" },
  ]

  const metrics = [
    { label: "CO₂e Sequestered", value: results.co2e_tonnes,                   unit: "tonnes CO₂e",  highlight: true },
    { label: "Project Area",      value: results.area_ha,                        unit: "hectares" },
    { label: "Baseline NDVI",     value: results.baseline_ndvi,                  unit: "index value" },
    { label: "Monitoring NDVI",   value: results.monitoring_ndvi,                unit: "index value" },
    { label: "NDVI Change",       value: results.ndvi_change,                    unit: "delta" },
    { label: "Carbon Sequestered",value: results.carbon_sequestered_tonnes_c,    unit: "tonnes C" },
  ]

  return (
    <div className="space-y-4">

      {/* Title */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">{results.project_name}</h2>
            <p className="text-xs text-forest-300 mt-0.5">{results.methodology}</p>
          </div>
          <span className="text-xs glass text-forest-200 border border-forest-600/40 px-3 py-1 rounded-full font-medium">
            ±{results.uncertainty_pct}% uncertainty
          </span>
        </div>
      </div>

      {/* AI Interpretation */}
      {formParams && (
        <AIInterpretation results={results} formParams={formParams} />
      )}

      {/* Key metrics — staggered fade-up */}
      <div className="grid grid-cols-2 gap-3">
        {metrics.map(({ label, value, unit, highlight }, i) => (
          <div
            key={label}
            className="animate-fade-up"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <MetricCard label={label} value={value} unit={unit} highlight={highlight} />
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-sm font-bold text-white mb-4">CO₂e Uncertainty Range</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#2d8653" }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#2d8653" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => v.toLocaleString()}
            />
            <Tooltip
              contentStyle={{
                background: "rgba(13,46,28,0.92)",
                border: "1px solid rgba(45,134,83,0.3)",
                borderRadius: "10px",
                color: "#fff",
                fontSize: "12px",
              }}
              formatter={(v) => [`${v.toLocaleString()} t CO₂e`]}
            />
            <ReferenceLine
              y={results.co2e_tonnes}
              stroke="#2d8653"
              strokeDasharray="4 4"
              label={{ value: "estimate", fill: "#2d8653", fontSize: 10 }}
            />
            <Bar dataKey="co2e" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Biomass coefficient */}
      {results.biomass_coefficient_used && (
        <div className="glass rounded-2xl p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-forest-300 uppercase tracking-wide">
              ML Biomass Coefficient
            </p>
            <p className="text-lg font-bold text-white">
              {results.biomass_coefficient_used} t/ha per NDVI unit
            </p>
          </div>
          <span className="text-xs glass text-blue-400 border border-blue-500/20 px-3 py-1 rounded-full">
            FIA Model
          </span>
        </div>
      )}

      {/* Audit hash */}
      <HashBadge hash={results.run_hash} />

      {/* Timestamp */}
      <p className="text-xs text-forest-400 text-center">
        Generated at {new Date(results.generated_at).toLocaleString()}
      </p>

    </div>
  )
}
