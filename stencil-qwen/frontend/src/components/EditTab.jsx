import React, { useState } from 'react'

export default function EditTab({
  selectedCount,
  onSelectAll,
  onClearSelection,
  onExcludeRestore,
  onDuplicate,
  onSplitGrid,
  onResetEdits,
  libraryPresets,
  isPlacementMode,
  onSetPlacementMode,
  onSetPlacementPreset,
}) {
  const [deltaX, setDeltaX] = useState(0)
  const [deltaY, setDeltaY] = useState(0)
  const [maxCellWidth, setMaxCellWidth] = useState(3.0)
  const [maxCellHeight, setMaxCellHeight] = useState(3.0)
  const [webX, setWebX] = useState(0.5)
  const [webY, setWebY] = useState(0.5)
  const [rotationDeg, setRotationDeg] = useState(0)
  const [minFragmentArea, setMinFragmentArea] = useState(0.02)
  const [selectedPreset, setSelectedPreset] = useState(0)
  const [presetRotation, setPresetRotation] = useState(0)

  const handleDuplicate = () => {
    onDuplicate(deltaX, deltaY)
    setDeltaX(0)
    setDeltaY(0)
  }

  const handleSplitGrid = () => {
    onSplitGrid({
      max_cell_width_mm: maxCellWidth,
      max_cell_height_mm: maxCellHeight,
      web_x_mm: webX,
      web_y_mm: webY,
      rotation_deg: rotationDeg,
      min_fragment_area_mm2: minFragmentArea,
    })
  }

  const handlePlaceByClick = () => {
    if (libraryPresets.length > 0) {
      onSetPlacementPreset({ ...libraryPresets[selectedPreset], rotation_deg: presetRotation })
      onSetPlacementMode(true)
    }
  }

  return (
    <div className="sidebar-section">
      {/* Selection Actions */}
      <div className="form-group">
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', textTransform: 'uppercase', color: '#8b949e' }}>
          Selection Actions
        </h3>
        <button
          className="button button-secondary"
          onClick={onExcludeRestore}
          disabled={selectedCount === 0}
        >
          ⊘ Exclude / Restore ({selectedCount})
        </button>
        <button
          className="button button-secondary"
          onClick={onSelectAll}
        >
          ✓ Select All
        </button>
        <button
          className="button button-secondary"
          onClick={onClearSelection}
        >
          ✗ Clear Selection
        </button>
      </div>

      {/* Duplicate */}
      <div className="form-group">
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', textTransform: 'uppercase', color: '#8b949e' }}>
          Duplicate Apertures
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <div>
            <label className="form-label">ΔX (mm)</label>
            <input
              type="number"
              className="form-input"
              value={deltaX}
              onChange={(e) => setDeltaX(parseFloat(e.target.value) || 0)}
              step="0.5"
            />
          </div>
          <div>
            <label className="form-label">ΔY (mm)</label>
            <input
              type="number"
              className="form-input"
              value={deltaY}
              onChange={(e) => setDeltaY(parseFloat(e.target.value) || 0)}
              step="0.5"
            />
          </div>
        </div>
        <button
          className="button button-secondary"
          onClick={handleDuplicate}
          disabled={selectedCount === 0}
        >
          📋 Duplicate Selected
        </button>
      </div>

      {/* Library Apertures */}
      <div className="form-group">
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', textTransform: 'uppercase', color: '#8b949e' }}>
          Library Apertures
        </h3>
        {isPlacementMode && (
          <div style={{
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid #f59e0b',
            borderRadius: '6px',
            padding: '0.75rem',
            marginBottom: '0.75rem',
            fontSize: '0.875rem',
            color: '#f59e0b',
            fontWeight: 500,
          }}>
            🎯 Placement mode active - click on canvas to place
          </div>
        )}
        <select
          className="form-select"
          value={selectedPreset}
          onChange={(e) => setSelectedPreset(parseInt(e.target.value))}
        >
          {libraryPresets.map((preset, idx) => (
            <option key={idx} value={idx}>
              {preset.name || `${preset.shape} (${preset.diameter || preset.width}mm)`}
            </option>
          ))}
        </select>
        <div style={{ marginTop: '0.5rem' }}>
          <label className="form-label">Rotation (°)</label>
          <input
            type="number"
            className="form-input"
            value={presetRotation}
            onChange={(e) => setPresetRotation(parseFloat(e.target.value) || 0)}
            step="15"
          />
        </div>
        <button
          className="button button-secondary"
          onClick={handlePlaceByClick}
        >
          🖱️ Place by Click
        </button>
      </div>

      {/* Grid Split */}
      <div className="form-group">
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', textTransform: 'uppercase', color: '#8b949e' }}>
          Grid Split
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <div>
            <label className="form-label">Max Cell Width (mm)</label>
            <input
              type="number"
              className="form-input"
              value={maxCellWidth}
              onChange={(e) => setMaxCellWidth(parseFloat(e.target.value) || 3.0)}
              step="0.5"
              min="0.1"
            />
          </div>
          <div>
            <label className="form-label">Max Cell Height (mm)</label>
            <input
              type="number"
              className="form-input"
              value={maxCellHeight}
              onChange={(e) => setMaxCellHeight(parseFloat(e.target.value) || 3.0)}
              step="0.5"
              min="0.1"
            />
          </div>
          <div>
            <label className="form-label">Web X (mm)</label>
            <input
              type="number"
              className="form-input"
              value={webX}
              onChange={(e) => setWebX(parseFloat(e.target.value) || 0.5)}
              step="0.1"
              min="0"
            />
          </div>
          <div>
            <label className="form-label">Web Y (mm)</label>
            <input
              type="number"
              className="form-input"
              value={webY}
              onChange={(e) => setWebY(parseFloat(e.target.value) || 0.5)}
              step="0.1"
              min="0"
            />
          </div>
        </div>
        <div style={{ marginTop: '0.5rem' }}>
          <label className="form-label">Rotation (°)</label>
          <input
            type="number"
            className="form-input"
            value={rotationDeg}
            onChange={(e) => setRotationDeg(parseFloat(e.target.value) || 0)}
            step="15"
          />
        </div>
        <div style={{ marginTop: '0.5rem' }}>
          <label className="form-label">Min Fragment Area (mm²)</label>
          <input
            type="number"
            className="form-input"
            value={minFragmentArea}
            onChange={(e) => setMinFragmentArea(parseFloat(e.target.value) || 0.02)}
            step="0.01"
            min="0"
          />
        </div>
        <button
          className="button button-secondary"
          onClick={handleSplitGrid}
          disabled={selectedCount === 0}
        >
          ⊞ Split Selected
        </button>
      </div>

      {/* Edit Management */}
      <div className="form-group">
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', textTransform: 'uppercase', color: '#8b949e' }}>
          Edit Management
        </h3>
        <button
          className="button button-danger"
          onClick={onResetEdits}
        >
          🔄 Reset All Edits
        </button>
      </div>
    </div>
  )
}
