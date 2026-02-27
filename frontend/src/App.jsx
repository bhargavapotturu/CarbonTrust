// src/App.jsx
import { useState } from "react"
import ForestForm from "./components/ForestForm"
import ResultsPanel from "./components/ResultsPanel"

export default function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  return (
    <div className="min-h-screen bg-forest-50 flex flex-col">
      {/* Header */}
      <header className="bg-forest-700 text-white px-8 py-4 flex items-center justify-between shadow-lg">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">🌲 CarbonTrust</h1>
          <p className="text-forest-100 text-sm">Satellite-Based Carbon Verification</p>
        </div>
        <span className="text-xs bg-forest-500 px-3 py-1 rounded-full font-medium">
          IPCC 2006 · Sentinel-2
        </span>
      </header>

      {/* Main */}
      <main className="flex flex-1 gap-6 p-6 max-w-7xl mx-auto w-full">
        {/* Left panel - Form */}
        <div className="w-full max-w-md flex-shrink-0">
          <ForestForm
            setResults={setResults}
            setLoading={setLoading}
            setError={setError}
            loading={loading}
          />
        </div>

        {/* Right panel - Results */}
        <div className="flex-1">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-4">
              {error}
            </div>
          )}
          {loading && (
            <div className="flex flex-col items-center justify-center h-64 text-forest-700">
              <div className="w-12 h-12 border-4 border-forest-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-sm font-medium">Analyzing satellite imagery...</p>
              <p className="text-xs text-gray-400 mt-1">This may take 20–30 seconds</p>
            </div>
          )}
          {results && !loading && (
            <ResultsPanel results={results} />
          )}
          {!results && !loading && !error && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <p className="text-4xl mb-3">🛰️</p>
              <p className="text-sm">Enter forest parameters and click Analyze</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}