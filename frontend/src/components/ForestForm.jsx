// src/components/ForestForm.jsx
import { useState } from "react"
import axios from "axios"

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
      <label className="block text-xs font-semibold text-gray-600 mb-1 uppercase tracking-wide">
        {label}
      </label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        step={step}
        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 bg-white"
      />
    </div>
  )
}

export default function ForestForm({ setResults, setLoading, setError, loading }) {
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
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">
      <div>
        <h2 className="text-lg font-bold text-forest-700">Project Parameters</h2>
        <p className="text-xs text-gray-400 mt-0.5">Configure your forest analysis</p>
      </div>

      {/* Project name */}
      <Field label="Project Name" name="project_name" value={form.project_name} onChange={handleChange} />

      {/* Bounding box */}
      <div>
        <p className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">
          Bounding Box
        </p>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Min Longitude" name="min_lon" value={form.min_lon} onChange={handleChange} type="number" step="0.01" />
          <Field label="Min Latitude" name="min_lat" value={form.min_lat} onChange={handleChange} type="number" step="0.01" />
          <Field label="Max Longitude" name="max_lon" value={form.max_lon} onChange={handleChange} type="number" step="0.01" />
          <Field label="Max Latitude" name="max_lat" value={form.max_lat} onChange={handleChange} type="number" step="0.01" />
        </div>
      </div>

      {/* Dates */}
      <div>
        <p className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">
          Baseline Period
        </p>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Start" name="baseline_start" value={form.baseline_start} onChange={handleChange} />
          <Field label="End" name="baseline_end" value={form.baseline_end} onChange={handleChange} />
        </div>
      </div>

      <div>
        <p className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">
          Monitoring Period
        </p>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Start" name="monitoring_start" value={form.monitoring_start} onChange={handleChange} />
          <Field label="End" name="monitoring_end" value={form.monitoring_end} onChange={handleChange} />
        </div>
      </div>

      {/* Forest attributes */}
      <div>
        <p className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">
          Forest Attributes
        </p>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1 uppercase tracking-wide">
              Forest Type
            </label>
            <select
              name="forest_type_code"
              value={form.forest_type_code}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 bg-white"
            >
              <option value={100}>Pine</option>
              <option value={200}>Spruce/Fir</option>
              <option value={400}>Oak/Hardwood</option>
              <option value={500}>Mixed Forest</option>
            </select>
          </div>
          <Field label="Canopy Cover %" name="canopy_cover_pct" value={form.canopy_cover_pct} onChange={handleChange} type="number" />
          <Field label="Stand Age (yrs)" name="stand_age" value={form.stand_age} onChange={handleChange} type="number" />
          <Field label="Basal Area (ft²/ac)" name="basal_area_live" value={form.basal_area_live} onChange={handleChange} type="number" />
        </div>
      </div>

      {/* Buttons */}
      <div className="flex gap-2 pt-2">
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="flex-1 bg-forest-700 hover:bg-forest-500 text-white font-semibold py-2.5 rounded-xl text-sm transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Analyzing..." : "🛰 Analyze"}
        </button>
        <button
          onClick={handleDownload}
          className="px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2.5 rounded-xl text-sm transition"
        >
          📄 PDF
        </button>
      </div>
    </div>
  )
}