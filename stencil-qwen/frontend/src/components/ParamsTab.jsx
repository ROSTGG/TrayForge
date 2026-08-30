import React from 'react'

export default function ParamsTab({ options, onOptionsChange }) {
  const handleChange = (key, value) => {
    onOptionsChange(prev => ({
      ...prev,
      [key]: value,
    }))
  }

  const handleCheckboxChange = (key) => {
    onOptionsChange(prev => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  return (
    <div className="sidebar-section">
      <div className="form-group">
        <label className="form-label">Thickness (mm)</label>
        <input
          type="number"
          className="form-input"
          value={options.thickness_mm}
          onChange={(e) => handleChange('thickness_mm', parseFloat(e.target.value) || 0)}
          step="0.01"
          min="0.01"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Margin (mm)</label>
        <input
          type="number"
          className="form-input"
          value={options.margin_mm}
          onChange={(e) => handleChange('margin_mm', parseFloat(e.target.value) || 0)}
          step="0.5"
          min="0"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Corner Radius (mm)</label>
        <input
          type="number"
          className="form-input"
          value={options.corner_radius_mm}
          onChange={(e) => handleChange('corner_radius_mm', parseFloat(e.target.value) || 0)}
          step="0.1"
          min="0"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Aperture Offset (mm)</label>
        <input
          type="number"
          className="form-input"
          value={options.aperture_offset_mm}
          onChange={(e) => handleChange('aperture_offset_mm', parseFloat(e.target.value) || 0)}
          step="0.01"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Arc Tolerance (mm)</label>
        <input
          type="number"
          className="form-input"
          value={options.arc_tolerance_mm}
          onChange={(e) => handleChange('arc_tolerance_mm', parseFloat(e.target.value) || 0)}
          step="0.001"
          min="0.001"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Sheet Width (mm) - leave blank for auto</label>
        <input
          type="number"
          className="form-input"
          value={options.sheet_width_mm || ''}
          onChange={(e) => handleChange('sheet_width_mm', e.target.value ? parseFloat(e.target.value) : null)}
          step="0.5"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Sheet Height (mm) - leave blank for auto</label>
        <input
          type="number"
          className="form-input"
          value={options.sheet_height_mm || ''}
          onChange={(e) => handleChange('sheet_height_mm', e.target.value ? parseFloat(e.target.value) : null)}
          step="0.5"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Rotation (°)</label>
        <input
          type="number"
          className="form-input"
          value={options.rotate_deg}
          onChange={(e) => handleChange('rotate_deg', parseFloat(e.target.value) || 0)}
          step="1"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Min Aperture Area (mm²)</label>
        <input
          type="number"
          className="form-input"
          value={options.min_opening_area_mm2}
          onChange={(e) => handleChange('min_opening_area_mm2', parseFloat(e.target.value) || 0)}
          step="0.01"
          min="0"
        />
      </div>

      <div className="checkbox-group">
        <input
          type="checkbox"
          id="mirror-x"
          checked={options.mirror_x}
          onChange={() => handleCheckboxChange('mirror_x')}
        />
        <label htmlFor="mirror-x">Mirror X</label>
      </div>

      <div className="checkbox-group">
        <input
          type="checkbox"
          id="mirror-y"
          checked={options.mirror_y}
          onChange={() => handleCheckboxChange('mirror_y')}
        />
        <label htmlFor="mirror-y">Mirror Y</label>
      </div>

      <div className="checkbox-group">
        <input
          type="checkbox"
          id="center-z"
          checked={options.center_z}
          onChange={() => handleCheckboxChange('center_z')}
        />
        <label htmlFor="center-z">Center Z (symmetric)</label>
      </div>
    </div>
  )
}
