import React, { useRef, useEffect, useState } from 'react'

export default function Canvas({
  apertures,
  addedApertures,
  selectedApertures,
  excludedIds,
  bounds,
  svg,
  onSelect,
  isPlacementMode,
  placementPreset,
  onPlaceAperture,
  isLoading,
}) {
  const canvasRef = useRef(null)
  const svgRef = useRef(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const pixelsPerMm = 12 // Conversion factor

  useEffect(() => {
    fitToView()
  }, [bounds])

  const fitToView = () => {
    if (!canvasRef.current) return
    const w = canvasRef.current.clientWidth
    const h = canvasRef.current.clientHeight
    if (bounds[2] - bounds[0] === 0 || bounds[3] - bounds[1] === 0) return

    const boundsWidth = bounds[2] - bounds[0]
    const boundsHeight = bounds[3] - bounds[1]
    const scaleX = (w * 0.9) / (boundsWidth * pixelsPerMm)
    const scaleY = (h * 0.9) / (boundsHeight * pixelsPerMm)
    const scale = Math.min(scaleX, scaleY)

    setZoom(scale)
    const centerX = (bounds[0] + bounds[2]) / 2
    const centerY = (bounds[1] + bounds[3]) / 2
    setPan({
      x: w / 2 - centerX * pixelsPerMm * scale,
      y: h / 2 - centerY * pixelsPerMm * scale,
    })
  }

  const handleWheel = (e) => {
    e.preventDefault()
    const rect = canvasRef.current.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top

    const delta = e.deltaY > 0 ? 0.8 : 1.2
    const newZoom = Math.max(0.1, Math.min(20, zoom * delta))
    const factor = newZoom / zoom

    const newPan = {
      x: mouseX - (mouseX - pan.x) * factor,
      y: mouseY - (mouseY - pan.y) * factor,
    }

    setZoom(newZoom)
    setPan(newPan)
  }

  const handleMouseDown = (e) => {
    if (e.button === 1 || (e.button === 0 && e.shiftKey && e.ctrlKey)) {
      // Middle button or Ctrl+Shift+Left = pan
      setIsPanning(true)
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    } else if (e.button === 0 && isPlacementMode && canvasRef.current) {
      // Left click in placement mode
      const rect = canvasRef.current.getBoundingClientRect()
      const screenX = e.clientX - rect.left
      const screenY = e.clientY - rect.top
      const worldX = (screenX - pan.x) / (zoom * pixelsPerMm)
      const worldY = (screenY - pan.y) / (zoom * pixelsPerMm)
      if (placementPreset) {
        onPlaceAperture(placementPreset, worldX, worldY)
      }
    }
  }

  const handleMouseMove = (e) => {
    if (isPanning) {
      setPan({
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y,
      })
    }

    if (canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect()
      const screenX = e.clientX - rect.left
      const screenY = e.clientY - rect.top
      const worldX = (screenX - pan.x) / (zoom * pixelsPerMm)
      const worldY = (screenY - pan.y) / (zoom * pixelsPerMm)
      setCursorPos({ x: worldX, y: worldY })
    }
  }

  const handleMouseUp = () => {
    setIsPanning(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      // Cancel placement mode
    } else if (e.key === 'f' || e.key === 'F' || e.key === 'Home') {
      fitToView()
    } else if (e.key === '+' || e.key === '=') {
      setZoom(z => Math.min(20, z * 1.2))
    } else if (e.key === '-') {
      setZoom(z => Math.max(0.1, z * 0.8))
    }
  }

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const allApertures = [...apertures, ...addedApertures]

  return (
    <div className="canvas-container">
      <div className="toolbar">
        <button className="zoom-button" onClick={() => setZoom(z => Math.max(0.1, z * 0.8))}>
          −
        </button>
        <button className="zoom-button" onClick={() => setZoom(z => Math.min(20, z * 1.2))}>
          +
        </button>
        <button className="zoom-button" onClick={fitToView}>
          Fit
        </button>
        <div style={{ marginLeft: 'auto', fontSize: '0.75rem', color: '#8b949e' }}>
          Zoom: {(zoom * 100).toFixed(0)}%
        </div>
      </div>

      <div
        className={`svg-canvas ${isPlacementMode ? 'placement-mode' : ''}`}
        ref={canvasRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isPlacementMode ? 'crosshair' : 'grab' }}
      >
        <svg
          ref={svgRef}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: '0 0',
            width: '100%',
            height: '100%',
          }}
        >
          {/* Sheet background */}
          {bounds[2] > bounds[0] && bounds[3] > bounds[1] && (
            <rect
              x={bounds[0]}
              y={bounds[1]}
              width={bounds[2] - bounds[0]}
              height={bounds[3] - bounds[1]}
              fill="none"
              stroke="#30363d"
              strokeWidth="0.1"
            />
          )}

          {/* Apertures */}
          {allApertures.map((aperture) => {
            const isSelected = selectedApertures.has(aperture.id)
            const isExcluded = excludedIds.has(aperture.id)
            const isAdded = aperture.type === 'added'

            return (
              <path
                key={aperture.id}
                d={polygonToPathD(aperture.polygon)}
                className={`aperture-path ${isAdded ? 'added' : ''} ${isSelected ? 'selected' : ''} ${isExcluded ? 'excluded' : ''}`}
                onClick={() => onSelect(aperture, false)}
                style={{ cursor: 'pointer' }}
              />
            )
          })}
        </svg>
      </div>

      <div className="status-bar">
        <span>Zoom: {(zoom * 100).toFixed(0)}% | {(zoom * pixelsPerMm).toFixed(1)} px/mm</span>
        <span>x: {cursorPos.x.toFixed(2)} mm | y: {cursorPos.y.toFixed(2)} mm</span>
      </div>
    </div>
  )
}

function polygonToPathD(coords) {
  if (!coords || coords.length === 0) return ''
  let d = `M ${coords[0][0]} ${coords[0][1]}`
  for (let i = 1; i < coords.length; i++) {
    d += ` L ${coords[i][0]} ${coords[i][1]}`
  }
  d += ' Z'
  return d
}
