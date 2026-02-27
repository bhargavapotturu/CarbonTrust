// src/components/MonitorPanel.jsx
import { useState, useEffect } from "react"
import axios from "axios"

const API_BASE = "http://localhost:8000"

const defaultForm = {
  name: "",
  description: "",
  bbox: [-80.1, 37.2, -79.8, 37.5],
  forest_type_code: 220,
  canopy_cover_pct: 60,
  stand_age: 40,
  basal_area_live: 25,
}

function SeverityBadge({ severity }) {
  const styles = {
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
    warning:  "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    info:     "bg-blue-500/20 text-blue-400 border-blue-500/30",
  }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${styles[severity] || "bg-white/10 text-forest-400 border-white/10"}`}>
      {severity?.toUpperCase()}
    </span>
  )
}

function ProjectCard({ project, onTrigger, onDelete }) {
  const [alerts, setAlerts] = useState([])
  const [triggering, setTriggering] = useState(false)

  useEffect(() => {
    axios.get(`${API_BASE}/projects/${project.id}/alerts`)
      .then(res => setAlerts(res.data))
      .catch(() => {})
  }, [project.id])

  const latestAlert = alerts[0] || null

  const handleTrigger = async () => {
    setTriggering(true)
    await onTrigger(project.id)
    const res = await axios.get(`${API_BASE}/projects/${project.id}/alerts`)
    setAlerts(res.data)
    setTriggering(false)
  }

  return (
    <div className="glass rounded-2xl p-5 space-y-3 hover:border-forest-700/60 transition-all duration-200">

      {/* Project header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-bold text-white">{project.name}</h3>
          <p className="text-xs text-forest-300 mt-0.5">{project.description || "No description"}</p>
        </div>
        <span className="text-xs font-mono glass text-forest-200 px-2 py-0.5 rounded">
          {project.id}
        </span>
      </div>

      {/* Bounding box */}
      <div className="text-xs text-forest-300 font-mono">
        [{project.bbox?.join(", ")}]
      </div>

      {/* Latest alert */}
      <div className="glass-dark rounded-xl p-3">
        <p className="text-xs font-semibold text-forest-200 uppercase tracking-wide mb-1">
          Latest Alert
        </p>
        {latestAlert ? (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <SeverityBadge severity={latestAlert.severity} />
              <span className="text-xs text-forest-200">
                {latestAlert.anomaly_type?.replace(/_/g, " ")}
              </span>
            </div>
            <p className="text-xs text-forest-300">{latestAlert.summary}</p>
            <p className="text-xs text-forest-400">
              NDVI: {latestAlert.ndvi_baseline} → {latestAlert.ndvi_current}{" "}
              ({latestAlert.ndvi_delta > 0 ? "+" : ""}{latestAlert.ndvi_delta})
            </p>
          </div>
        ) : (
          <p className="text-xs text-forest-300">No anomalies detected</p>
        )}
      </div>

      {alerts.length > 1 && (
        <p className="text-xs text-forest-400">{alerts.length} total alerts</p>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={handleTrigger}
          disabled={triggering}
          className="flex-1 gradient-carbon hover:opacity-90 text-white text-xs font-semibold py-2 rounded-lg transition-all duration-200 disabled:opacity-40"
        >
          {triggering ? "Running..." : "Run Monitor"}
        </button>
        <button
          onClick={() => onDelete(project.id)}
          className="px-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold py-2 rounded-lg transition-all duration-200 border border-red-500/20"
        >
          Delete
        </button>
      </div>
    </div>
  )
}

export default function MonitorPanel() {
  const [projects, setProjects] = useState([])
  const [form, setForm] = useState(defaultForm)
  const [bboxInput, setBboxInput] = useState("-80.1, 37.2, -79.8, 37.5")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const res = await axios.get(`${API_BASE}/projects`)
      setProjects(res.data)
    } catch {
      setError("Could not load projects.")
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({
      ...prev,
      [name]: isNaN(value) || value === "" ? value : Number(value),
    }))
  }

  const handleRegister = async () => {
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      const bbox = bboxInput.split(",").map(v => parseFloat(v.trim()))
      if (bbox.length !== 4 || bbox.some(isNaN)) {
        setError("Bounding box must be 4 numbers: min_lon, min_lat, max_lon, max_lat")
        return
      }
      await axios.post(`${API_BASE}/projects`, { ...form, bbox })
      setSuccess(`Project "${form.name}" registered successfully.`)
      setForm(defaultForm)
      setBboxInput("-80.1, 37.2, -79.8, 37.5")
      fetchProjects()
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to register project.")
    } finally {
      setLoading(false)
    }
  }

  const handleTrigger = async (projectId) => {
    try {
      await axios.post(`${API_BASE}/monitor/trigger/${projectId}`)
    } catch {
      setError("Monitor trigger failed.")
    }
  }

  const handleDelete = async (projectId) => {
    try {
      await axios.delete(`${API_BASE}/projects/${projectId}`)
      fetchProjects()
    } catch {
      setError("Failed to delete project.")
    }
  }

  const inputClass = "w-full px-3 py-2 input-dark rounded-lg text-sm"
  const labelClass = "block text-xs font-semibold text-forest-100 mb-1 uppercase tracking-wide"

  return (
    <div className="w-full flex gap-6 animate-fade-up">

      {/* Left — Register form */}
      <div className="w-full max-w-sm flex-shrink-0">
        <div className="glass-dark rounded-2xl p-6 space-y-4">
          <div>
            <h2 className="text-base font-bold text-white">Register Project</h2>
            <p className="text-xs text-forest-300 mt-0.5">Add a forest to monitor</p>
          </div>

          {error   && <p className="text-xs text-red-400 glass rounded-lg p-2">{error}</p>}
          {success && <p className="text-xs text-forest-200 glass rounded-lg p-2">{success}</p>}

          {[
            { label: "Project Name", name: "name",        type: "text" },
            { label: "Description",  name: "description", type: "text" },
          ].map(f => (
            <div key={f.name}>
              <label className={labelClass}>{f.label}</label>
              <input
                type={f.type}
                name={f.name}
                value={form[f.name]}
                onChange={handleChange}
                className={inputClass}
              />
            </div>
          ))}

          <div>
            <label className={labelClass}>Bounding Box (min_lon, min_lat, max_lon, max_lat)</label>
            <input
              type="text"
              value={bboxInput}
              onChange={e => setBboxInput(e.target.value)}
              className={inputClass}
            />
          </div>

          {[
            { label: "Canopy Cover %",    name: "canopy_cover_pct" },
            { label: "Stand Age (yrs)",   name: "stand_age" },
            { label: "Basal Area (ft²/ac)", name: "basal_area_live" },
          ].map(f => (
            <div key={f.name}>
              <label className={labelClass}>{f.label}</label>
              <input
                type="number"
                name={f.name}
                value={form[f.name]}
                onChange={handleChange}
                className={inputClass}
              />
            </div>
          ))}

          <div>
            <label className={labelClass}>Forest Type</label>
            <select
              name="forest_type_code"
              value={form.forest_type_code}
              onChange={handleChange}
              className="w-full px-3 py-2 input-dark rounded-lg text-sm"
            >
              <option value={100}  className="bg-forest-900">Pine</option>
              <option value={200}  className="bg-forest-900">Spruce/Fir</option>
              <option value={220}  className="bg-forest-900">Loblolly Pine</option>
              <option value={400}  className="bg-forest-900">Oak/Hardwood</option>
              <option value={500}  className="bg-forest-900">Mixed Forest</option>
            </select>
          </div>

          <button
            onClick={handleRegister}
            disabled={loading || !form.name}
            className="w-full gradient-carbon hover:opacity-90 text-white font-semibold py-2.5 rounded-xl text-sm transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? "Registering..." : "Register Project"}
          </button>
        </div>
      </div>

      {/* Right — Project list */}
      <div className="flex-1">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-white">
            Monitored Projects
            <span className="ml-2 text-sm font-normal text-forest-300">({projects.length})</span>
          </h2>
          <button
            onClick={fetchProjects}
            className="text-xs text-forest-300 hover:text-forest-200 glass px-3 py-1 rounded-lg transition-all duration-150"
          >
            Refresh
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-forest-300">
            <div className="w-16 h-16 rounded-2xl glass flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-forest-300" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
            </div>
            <p className="text-sm text-forest-300">No projects registered yet</p>
            <p className="text-xs text-forest-400 mt-1">Use the form to add your first forest project</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {projects.map((project, i) => (
              <div
                key={project.id}
                className="animate-fade-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <ProjectCard
                  project={project}
                  onTrigger={handleTrigger}
                  onDelete={handleDelete}
                />
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}
