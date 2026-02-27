// src/components/ResultsPanel.jsx
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts"

function MetricCard({ label, value, unit, highlight }) {
  return (
    <div className={`rounded-xl p-4 border ${highlight ? "bg-forest-700 text-white border-forest-700" : "bg-white border-gray-100"}`}>
      <p className={`text-xs font-semibold uppercase tracking-wide mb-1 ${highlight ? "text-forest-100" : "text-gray-400"}`}>
        {label}
      </p>
      <p className={`text-2xl font-bold ${highlight ? "text-white" : "text-forest-700"}`}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      <p className={`text-xs mt-0.5 ${highlight ? "text-forest-100" : "text-gray-400"}`}>
        {unit}
      </p>
    </div>
  )
}

function HashBadge({ hash }) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
        SHA-256 Run Hash
      </p>
      <p className="text-xs font-mono text-gray-600 break-all">{hash}</p>
    </div>
  )
}

export default function ResultsPanel({ results }) {
  const chartData = [
    {
      name: "Low (−20%)",
      co2e: results.co2e_low,
      fill: "#d8eedf",
    },
    {
      name: "Estimate",
      co2e: results.co2e_tonnes,
      fill: "#1a5c38",
    },
    {
      name: "High (+20%)",
      co2e: results.co2e_high,
      fill: "#d8eedf",
    },
  ]

  return (
    <div className="space-y-4">
      {/* Title */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-forest-700">{results.project_name}</h2>
            <p className="text-xs text-gray-400 mt-0.5">{results.methodology}</p>
          </div>
          <span className="text-xs bg-forest-50 text-forest-700 border border-forest-100 px-3 py-1 rounded-full font-medium">
            ±{results.uncertainty_pct}% uncertainty
          </span>
        </div>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          label="CO₂e Sequestered"
          value={results.co2e_tonnes}
          unit="tonnes CO₂e"
          highlight
        />
        <MetricCard
          label="Project Area"
          value={results.area_ha}
          unit="hectares"
        />
        <MetricCard
          label="Baseline NDVI"
          value={results.baseline_ndvi}
          unit="index value"
        />
        <MetricCard
          label="Monitoring NDVI"
          value={results.monitoring_ndvi}
          unit="index value"
        />
        <MetricCard
          label="NDVI Change"
          value={results.ndvi_change}
          unit="delta"
        />
        <MetricCard
          label="Carbon Sequestered"
          value={results.carbon_sequestered_tonnes_c}
          unit="tonnes C"
        />
      </div>

      {/* Chart */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h3 className="text-sm font-bold text-gray-700 mb-4">CO₂e Uncertainty Range</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => v.toLocaleString()} />
            <Tooltip formatter={(v) => [`${v.toLocaleString()} t CO₂e`]} />
            <ReferenceLine
              y={results.co2e_tonnes}
              stroke="#1a5c38"
              strokeDasharray="4 4"
            />
            <Bar dataKey="co2e" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, i) => (
                <rect key={i} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Biomass coefficient if present */}
      {results.biomass_coefficient_used && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              ML Biomass Coefficient
            </p>
            <p className="text-lg font-bold text-forest-700">
              {results.biomass_coefficient_used} t/ha per NDVI unit
            </p>
          </div>
          <span className="text-xs bg-blue-50 text-blue-600 border border-blue-100 px-3 py-1 rounded-full">
            FIA Model
          </span>
        </div>
      )}

      {/* Audit hash */}
      <HashBadge hash={results.run_hash} />

      {/* Timestamp */}
      <p className="text-xs text-gray-400 text-center">
        Generated at {new Date(results.generated_at).toLocaleString()}
      </p>
    </div>
  )
}