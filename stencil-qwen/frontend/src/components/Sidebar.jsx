import React, { useState } from 'react'
import ParamsTab from './ParamsTab'
import EditTab from './EditTab'

export default function Sidebar({
  selectedCount,
  onFileUpload,
  onSelectAll,
  onClearSelection,
  onExcludeRestore,
  onDuplicate,
  onSplitGrid,
  onResetEdits,
  onConvert,
  libraryPresets,
  isPlacementMode,
  onSetPlacementMode,
  onSetPlacementPreset,
  isConverting,
  isLoading,
}) {
  const [activeTab, setActiveTab] = useState('params')
  const [options, setOptions] = useState({
    thickness_mm: 0.12,
    margin_mm: 10.0,
    corner_radius_mm: 2.0,
    aperture_offset_mm: 0.0,
    arc_tolerance_mm: 0.01,
    sheet_width_mm: null,
    sheet_height_mm: null,
    mirror_x: false,
    mirror_y: false,
    rotate_deg: 0.0,
    center_z: false,
    min_opening_area_mm2: 0.0,
    precision_grid_mm: 1e-6,
  })
  const [dragOver, setDragOver] = useState(false)

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) onFileUpload(file)
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) onFileUpload(file)
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <div
          className={`upload-zone ${dragOver ? 'dragover' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.querySelector('#file-input')?.click()}
        >
          <div className="upload-icon">📁</div>
          <div className="upload-text">
            Drop Gerber file here
            <br />
            or click to browse
          </div>
        </div>
        <input
          id="file-input"
          type="file"
          accept=".gtp,.gbp,.gbr,.ger,.gerber"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />
      </div>

      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'params' ? 'active' : ''}`}
          onClick={() => setActiveTab('params')}
        >
          Params
        </button>
        <button
          className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`}
          onClick={() => setActiveTab('edit')}
        >
          Edit
        </button>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {activeTab === 'params' && (
          <ParamsTab options={options} onOptionsChange={setOptions} />
        )}
        {activeTab === 'edit' && (
          <EditTab
            selectedCount={selectedCount}
            onSelectAll={onSelectAll}
            onClearSelection={onClearSelection}
            onExcludeRestore={onExcludeRestore}
            onDuplicate={onDuplicate}
            onSplitGrid={onSplitGrid}
            onResetEdits={onResetEdits}
            libraryPresets={libraryPresets}
            isPlacementMode={isPlacementMode}
            onSetPlacementMode={onSetPlacementMode}
            onSetPlacementPreset={onSetPlacementPreset}
          />
        )}
      </div>

      <button
        className="convert-button"
        onClick={() => onConvert(options)}
        disabled={isConverting || isLoading}
      >
        {isConverting ? (
          <>
            <span className="spinner"></span> Converting...
          </>
        ) : (
          '⬇️ Convert to STL'
        )}
      </button>
    </aside>
  )
}
