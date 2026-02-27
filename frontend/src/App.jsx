// src/App.jsx
import { useState } from "react"
import ForestForm from "./components/ForestForm"
import ResultsPanel from "./components/ResultsPanel"
import MonitorPanel from "./components/MonitorPanel"

function IconLeaf({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
    </svg>
  )
}

function IconSatellite({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 7 9 3 5 7l4 4"/>
      <path d="m17 11 4 4-4 4-4-4"/>
      <path d="m8 12 4 4 6-6-4-4Z"/>
      <path d="m16 8 3-3"/>
      <path d="M9 21a6 6 0 0 0-6-6"/>
    </svg>
  )
}

function IconMonitor({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  )
}

export default function App() {
  const [tab, setTab] = useState("analyze")
  const [results, setResults] = useState(null)
  const [formParams, setFormParams] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const navItems = [
    { id: "analyze", label: "Analyze", Icon: IconSatellite },
    { id: "monitor", label: "Monitor", Icon: IconMonitor },
  ]

  return (
    <div className="flex h-screen overflow-hidden font-sans">

      {/* ── SIDEBAR ─────────────────────────────────────────────── */}
      <aside className="w-60 flex-shrink-0 flex flex-col bg-forest-900 border-r border-forest-800">

        {/* Logo */}
        <div className="px-6 py-7 border-b border-forest-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg gradient-carbon flex items-center justify-center shadow-lg shadow-forest-950/50">
              <IconLeaf className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-white font-bold text-sm leading-tight">CarbonTrust</p>
              <p className="text-forest-300 text-xs leading-tight">Carbon Verification</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                tab === id
                  ? "bg-forest-700 text-white shadow-md shadow-forest-950/50"
                  : "text-forest-200 hover:bg-forest-800 hover:text-white"
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
              {tab === id && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-forest-500" />
              )}
            </button>
          ))}
        </nav>

        {/* Bottom badge */}
        <div className="px-4 pb-6">
          <div className="glass-dark rounded-xl px-3 py-3 text-center">
            <p className="text-forest-300 text-xs font-medium">IPCC 2006</p>
            <p className="text-forest-400 text-xs">Sentinel-2 · ML Coeff</p>
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT ─────────────────────────────────────────── */}
      <main className="flex-1 bg-forest-950 overflow-y-auto">
        <div className="p-6 max-w-7xl mx-auto">

          {/* Page header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-bold text-white">
                {tab === "analyze" ? "Carbon Analysis" : "Project Monitor"}
              </h1>
              <p className="text-forest-300 text-xs mt-0.5">
                {tab === "analyze"
                  ? "Estimate CO₂e sequestration from satellite NDVI"
                  : "Register and monitor active forest projects"}
              </p>
            </div>
            <span className="text-xs glass text-forest-200 px-3 py-1 rounded-full">
              v1.0 · {new Date().getFullYear()}
            </span>
          </div>

          {/* Tab content — key forces remount + re-triggers animate-fade-up */}
          <div key={tab} className="animate-fade-up">

            {/* Analyze Tab */}
            {tab === "analyze" && (
              <div className="flex gap-6 items-start">
                <div className="w-full max-w-md flex-shrink-0">
                  <ForestForm
                    setResults={setResults}
                    setFormParams={setFormParams}
                    setLoading={setLoading}
                    setError={setError}
                    loading={loading}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  {error && (
                    <div className="glass border-red-500/30 text-red-400 rounded-xl p-4 mb-4 text-sm">
                      {error}
                    </div>
                  )}
                  {loading && (
                    <div className="flex flex-col items-center justify-center h-64 text-forest-300">
                      <div className="w-10 h-10 border-2 border-forest-400 border-t-transparent rounded-full animate-spin mb-4" />
                      <p className="text-sm font-medium text-white">Analyzing satellite imagery...</p>
                      <p className="text-xs text-forest-300 mt-1">This may take 20–30 seconds</p>
                    </div>
                  )}
                  {results && !loading && (
                    <ResultsPanel results={results} formParams={formParams} />
                  )}
                  {!results && !loading && !error && (
                    <div className="flex flex-col items-center justify-center h-64 text-forest-300">
                      <div className="w-16 h-16 rounded-2xl glass flex items-center justify-center mb-4">
                        <IconSatellite className="w-8 h-8 text-forest-300" />
                      </div>
                      <p className="text-sm text-forest-300">Enter forest parameters and click Analyze</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Monitor Tab */}
            {tab === "monitor" && <MonitorPanel />}

          </div>
        </div>
      </main>

    </div>
  )
}
