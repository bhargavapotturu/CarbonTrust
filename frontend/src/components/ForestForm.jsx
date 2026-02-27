// src/components/ForestForm.jsx
import { useState, useEffect } from "react"
import axios from "axios"
import { MapContainer, TileLayer, Rectangle, useMap } from "react-leaflet"

const API_BASE = "http://localhost:8000"

const defaultForm = {
  project_name: "George Washington National Forest",
  min_lon: -79.5,
  min_lat: 38.0,
  max_lon: -78.5,
  max_lat: 38.5,
  baseline_start: "2021-06-01",
  baseline_end: "2021-09-01",
  monitoring_start: "2023-06-01",
  monitoring_end: "2023-09-01",
  forest_type_code: 400,
  canopy_cover_pct: 70,
  stand_age: 45,
  basal_area_live: 90,
}

function Field({ label, name, value, onChange, type = "text", step }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-forest-100 mb-1 uppercase tracking-wide">
        {label}
      </label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        step={step}
        className="w-full px-3 py-2 input-dark rounded-lg text-sm"
      />
    </div>
  )
}

// Re-centres the map whenever bounds change
function FitBounds({ bounds }) {
  const map = useMap()
  useEffect(() => {
    map.fitBounds(bounds, { padding: [20, 20] })
  }, [bounds, map])
  return null
}

function BboxMap({ minLon, minLat, maxLon, maxLat }) {
  const isValid =
    !isNaN(minLon) && !isNaN(minLat) &&
    !isNaN(maxLon) && !isNaN(maxLat) &&
    maxLat > minLat && maxLon > minLon

  if (!isValid) {
    return (
      <div className="h-40 glass rounded-xl flex items-center justify-center">
        <p className="text-xs text-forest-300">Enter valid coordinates to preview</p>
      </div>
    )
  }

  // react-leaflet uses [lat, lon] order
  const bounds = [
    [minLat, minLon],
    [maxLat, maxLon],
  ]

  return (
    <div className="h-48 rounded-xl overflow-hidden border border-forest-700/40">
      <MapContainer
        bounds={bounds}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%", background: "#0d2e1c" }}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        <Rectangle
          bounds={bounds}
          pathOptions={{
            color: "#2d8653",
            fillColor: "#1a5c38",
            fillOpacity: 0.25,
            weight: 2,
          }}
        />
        <FitBounds bounds={bounds} />
      </MapContainer>
    </div>
  )
}

export default function ForestForm({ setResults, setFormParams, setLoading, setError, loading }) {
  const [form, setForm] = useState(defaultForm)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: isNaN(value) || value === "" ? value : Number(value),
    }))
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const { data } = await axios.post(`${API_BASE}/estimate`, form)
      setResults(data)
      setFormParams(form)
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to connect to the API. Is the backend running?"
      )
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      const response = await axios.post(`${API_BASE}/report`, form, {
        responseType: "blob",
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement("a")
      link.href = url
      link.setAttribute("download", `${form.project_name.replace(/ /g, "_")}_report.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      setError("Failed to generate report.")
    }
  }

  return (
    <div className="glass-dark rounded-2xl p-6 space-y-5">
      <div>
        <h2 className="text-base font-bold text-white">Project Parameters</h2>
        <p className="text-xs text-forest-300 mt-0.5">Configure your forest analysis</p>
      </div>

      <Field label="Project Name" name="project_name" value={form.project_name} onChange={handleChange} />

      {/* Bounding Box */}
      <div>
        <p className="text-xs font-semibold text-forest-100 mb-2 uppercase tracking-wide">Bounding Box</p>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Min Longitude" name="min_lon" value={form.min_lon} onChange={handleChange} type="number" step="0.01" />
          <Field label="Min Latitude" name="min_lat" value={form.min_lat} onChange={handleChange} type="number" step="0.01" />
          <Field label="Max Longitude" name="max_lon" value={form.max_lon} onChange={handleChange} type="number" step="0.01" />
          <Field label="Max Latitude" name="max_lat" value={form.max_lat} onChange={handleChange} type="number" step="0.01" />
        </div>
        <div className="mt-3">
          <p className="text-xs font-semibold text-forest-100 mb-2 uppercase tracking-wide">Region Preview</p>
          <BboxMap
            minLon={form.min_lon}
            minLat={form.min_lat}
            maxLon={form.max_lon}
            maxLat={form.max_lat}
          />
        </div>
      </div>

      {/* Baseline Period */}
      <div>
        <p className="text-xs font-semibold text-forest-100 mb-2 uppercase tracking-wide">Baseline Period</p>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Start" name="baseline_start" value={form.baseline_start} onChange={handleChange} />
          <Field label="End" name="baseline_end" value={form.baseline_end} onChange={handleChange} />
        </div>
      </div>

      {/* Monitoring Period */}
      <div>
        <p className="text-xs font-semibold text-forest-100 mb-2 uppercase tracking-wide">Monitoring Period</p>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Start" name="monitoring_start" value={form.monitoring_start} onChange={handleChange} />
          <Field label="End" name="monitoring_end" value={form.monitoring_end} onChange={handleChange} />
        </div>
      </div>

      {/* Forest Attributes */}
      <div>
        <p className="text-xs font-semibold text-forest-100 mb-2 uppercase tracking-wide">Forest Attributes</p>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-semibold text-forest-100 mb-1 uppercase tracking-wide">
              Forest Type
            </label>
            <select
              name="forest_type_code"
              value={form.forest_type_code}
              onChange={handleChange}
              className="w-full px-3 py-2 input-dark rounded-lg text-sm"
            >
              <option value={100} className="bg-forest-900">Pine</option>
              <option value={200} className="bg-forest-900">Spruce/Fir</option>
              <option value={400} className="bg-forest-900">Oak/Hardwood</option>
              <option value={500} className="bg-forest-900">Mixed Forest</option>
            </select>
          </div>
          <Field label="Canopy Cover %" name="canopy_cover_pct" value={form.canopy_cover_pct} onChange={handleChange} type="number" />
          <Field label="Stand Age (yrs)" name="stand_age" value={form.stand_age} onChange={handleChange} type="number" />
          <Field label="Basal Area (ft²/ac)" name="basal_area_live" value={form.basal_area_live} onChange={handleChange} type="number" />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 pt-2">
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="flex-1 gradient-carbon hover:opacity-90 text-white font-semibold py-2.5 rounded-xl text-sm transition-all duration-200 shadow-lg shadow-forest-950/50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
        <button
          onClick={handleDownload}
          className="px-4 glass hover:bg-white/10 text-forest-300 font-semibold py-2.5 rounded-xl text-sm transition-all duration-200"
        >
          PDF
        </button>
      </div>
    </div>
  )
}
