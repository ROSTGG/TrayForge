import React, { useState, useRef, useEffect, useCallback } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Canvas from './components/Canvas'
import LogPanel from './components/LogPanel'
import ConversionModal from './components/ConversionModal'
import Toast from './components/Toast'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [apertures, setApertures] = useState([])
  const [svg, setSvg] = useState('')
  const [bounds, setBounds] = useState([0, 0, 100, 100])
  const [selectedApertures, setSelectedApertures] = useState(new Set())
  const [excludedIds, setExcludedIds] = useState(new Set())
  const [addedApertures, setAddedApertures] = useState([])
  const [libraryPresets, setLibraryPresets] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isConverting, setIsConverting] = useState(false)
  const [logs, setLogs] = useState([])
  const [toast, setToast] = useState(null)
  const [conversionReport, setConversionReport] = useState(null)
  const [isPlacementMode, setIsPlacementMode] = useState(false)
  const [placementPreset, setPlacementPreset] = useState(null)
  const fileInputRef = useRef(null)

  // Fetch library presets on mount
  useEffect(() => {
    fetchLibrary()
  }, [])

  const fetchLibrary = async () => {
    try {
      const res = await fetch('/api/library')
      const data = await res.json()
      setLibraryPresets(data.presets || [])
    } catch (err) {
      addLog('error', `Failed to fetch library: ${err.message}`)
    }
  }

  const addLog = (level, message) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, { level, message, timestamp }])
  }

  const showToast = (message, type = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const handleFileUpload = async (file) => {
    if (!file) return

    setIsLoading(true)
    addLog('info', `Uploading ${file.name}...`)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('arc_tolerance_mm', 0.01)
      formData.append('precision_grid_mm', 1e-6)

      const res = await fetch('/api/preview', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || 'Upload failed')
      }

      const data = await res.json()
      setSessionId(data.session_id)
      setApertures(data.apertures || [])
      setSvg(data.svg || '')
      setBounds(data.bounds || [0, 0, 100, 100])
      setSelectedApertures(new Set())
      setExcludedIds(new Set())
      setAddedApertures([])
      addLog('success', `Loaded ${data.apertures?.length || 0} apertures`)
    } catch (err) {
      addLog('error', err.message)
      showToast(err.message, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCanvasSelect = (aperture, multiSelect = false) => {
    setSelectedApertures(prev => {
      const next = new Set(prev)
      if (multiSelect) {
        if (next.has(aperture.id)) {
          next.delete(aperture.id)
        } else {
          next.add(aperture.id)
        }
      } else {
        if (prev.has(aperture.id) && prev.size === 1) {
          next.clear()
        } else {
          next.clear()
          next.add(aperture.id)
        }
      }
      return next
    })
  }

  const handleExcludeRestore = (ids = null) => {
    const toToggle = ids || selectedApertures
    setExcludedIds(prev => {
      const next = new Set(prev)
      for (const id of toToggle) {
        if (next.has(id)) {
          next.delete(id)
        } else {
          next.add(id)
        }
      }
      return next
    })
  }

  const handleSelectAll = () => {
    const allIds = new Set([
      ...apertures.map(a => a.id),
      ...addedApertures.map(a => a.id),
    ])
    setSelectedApertures(allIds)
  }

  const handleClearSelection = () => {
    setSelectedApertures(new Set())
  }

  const handleDuplicate = (deltaX, deltaY) => {
    const newApertures = []
    for (const id of selectedApertures) {
      const aperture = [...apertures, ...addedApertures].find(a => a.id === id)
      if (aperture) {
        const newPolygon = aperture.polygon.map(([x, y]) => [x + deltaX, y + deltaY])
        newApertures.push({
          id: `added:${Math.random().toString(36).substr(2, 9)}`,
          polygon: newPolygon,
          type: 'added',
          area_mm2: aperture.area_mm2,
          bounds: [
            aperture.bounds[0] + deltaX,
            aperture.bounds[1] + deltaY,
            aperture.bounds[2] + deltaX,
            aperture.bounds[3] + deltaY,
          ],
          centroid: [aperture.centroid[0] + deltaX, aperture.centroid[1] + deltaY],
        })
      }
    }
    setAddedApertures(prev => [...prev, ...newApertures])
    addLog('info', `Duplicated ${newApertures.length} apertures`)
  }

  const handlePlaceLibraryAperture = (preset, x, y) => {
    setIsPlacementMode(false)
    placeLibraryAperture(preset, x, y)
  }

  const placeLibraryAperture = async (preset, x, y) => {
    try {
      const res = await fetch('/api/library-aperture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preset,
          center_x: x,
          center_y: y,
          rotation_deg: 0,
          arc_tolerance_mm: 0.01,
        }),
      })

      if (!res.ok) throw new Error('Failed to create aperture')

      const data = await res.json()
      setAddedApertures(prev => [...prev, data])
      addLog('success', 'Placed library aperture')
    } catch (err) {
      addLog('error', err.message)
      showToast(err.message, 'error')
    }
  }

  const handleSplitGrid = async (params) => {
    const selectedList = Array.from(selectedApertures)
    if (selectedList.length === 0) {
      showToast('Select apertures to split', 'warning')
      return
    }

    addLog('info', `Splitting ${selectedList.length} apertures...`)

    try {
      const newFragments = []
      for (const id of selectedList) {
        const aperture = [...apertures, ...addedApertures].find(a => a.id === id)
        if (!aperture) continue

        const res = await fetch('/api/split-grid', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            polygon: aperture.polygon,
            ...params,
          }),
        })

        if (!res.ok) throw new Error('Split failed')
        const data = await res.json()
        newFragments.push(...data.fragments)
      }

      // Remove selected apertures, add fragments
      setApertures(prev => prev.filter(a => !selectedList.includes(a.id)))
      setAddedApertures(prev => [
        ...prev.filter(a => !selectedList.includes(a.id)),
        ...newFragments,
      ])
      setSelectedApertures(new Set())
      addLog('success', `Created ${newFragments.length} fragments`)
    } catch (err) {
      addLog('error', err.message)
      showToast(err.message, 'error')
    }
  }

  const handleResetEdits = () => {
    setExcludedIds(new Set())
    setAddedApertures([])
    setSelectedApertures(new Set())
    addLog('info', 'Reset all edits')
  }

  const handleConvert = async (options) => {
    if (!sessionId) {
      showToast('Please upload a file first', 'warning')
      return
    }

    setIsConverting(true)
    addLog('info', 'Starting conversion...')

    try {
      // We need to re-upload the file for conversion
      // For now, we'll create a dummy file from the parsed data
      const fileInput = document.querySelector('input[type="file"]')
      const file = fileInput?.files?.[0]

      if (!file) {
        throw new Error('File not found. Please upload again.')
      }

      const formData = new FormData()
      formData.append('file', file)
      formData.append('options', JSON.stringify(options))
      formData.append('excluded_ids', JSON.stringify(Array.from(excludedIds)))
      formData.append('added_apertures', JSON.stringify(addedApertures.map(a => a.polygon)))

      const res = await fetch('/api/convert', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || 'Conversion failed')
      }

      // Get report from header
      const reportHeader = res.headers.get('X-Conversion-Report')
      if (reportHeader) {
        try {
          const reportStr = decodeURIComponent(reportHeader)
          const report = JSON.parse(reportStr)
          setConversionReport(report)
        } catch (e) {
          console.error('Failed to parse report:', e)
        }
      }

      // Download STL
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'stencil.stl'
      link.click()
      URL.revokeObjectURL(url)

      addLog('success', 'Conversion complete! STL downloaded.')
      showToast('STL file downloaded successfully!', 'success')
    } catch (err) {
      addLog('error', err.message)
      showToast(err.message, 'error')
    } finally {
      setIsConverting(false)
    }
  }

  return (
    <div className="app">
      <Header />
      <div className="app-container">
        <Sidebar
          selectedCount={selectedApertures.size}
          onFileUpload={handleFileUpload}
          onSelectAll={handleSelectAll}
          onClearSelection={handleClearSelection}
          onExcludeRestore={() => handleExcludeRestore()}
          onDuplicate={handleDuplicate}
          onSplitGrid={handleSplitGrid}
          onResetEdits={handleResetEdits}
          onConvert={handleConvert}
          libraryPresets={libraryPresets}
          isPlacementMode={isPlacementMode}
          onSetPlacementMode={setIsPlacementMode}
          onSetPlacementPreset={setPlacementPreset}
          isConverting={isConverting}
          isLoading={isLoading}
        />
        <div className="main-area">
          <Canvas
            apertures={apertures}
            addedApertures={addedApertures}
            selectedApertures={selectedApertures}
            excludedIds={excludedIds}
            bounds={bounds}
            svg={svg}
            onSelect={handleCanvasSelect}
            isPlacementMode={isPlacementMode}
            placementPreset={placementPreset}
            onPlaceAperture={handlePlaceLibraryAperture}
            isLoading={isLoading}
          />
          <LogPanel logs={logs} />
        </div>
      </div>
      {conversionReport && (
        <ConversionModal
          report={conversionReport}
          onClose={() => setConversionReport(null)}
        />
      )}
      {toast && <Toast message={toast.message} type={toast.type} />}
      <input
        ref={fileInputRef}
        type="file"
        accept=".gtp,.gbp,.gbr,.ger,.gerber"
        style={{ display: 'none' }}
        onChange={(e) => handleFileUpload(e.target.files?.[0])}
      />
    </div>
  )
}

export default App
