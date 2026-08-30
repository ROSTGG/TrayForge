import React from 'react'

export default function ConversionModal({ report, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">✅ Conversion Report</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-content">
          <table className="report-table">
            <tbody>
              <tr>
                <th>Field</th>
                <th>Value</th>
              </tr>
              <tr>
                <td>Input File</td>
                <td>{report.input_file || 'N/A'}</td>
              </tr>
              <tr>
                <td>Output File</td>
                <td>{report.output_file}</td>
              </tr>
              <tr>
                <td>Primitives</td>
                <td>{report.primitive_count}</td>
              </tr>
              <tr>
                <td>Total Apertures</td>
                <td>{report.opening_count}</td>
              </tr>
              <tr>
                <td>Excluded</td>
                <td>{report.excluded_opening_count}</td>
              </tr>
              <tr>
                <td>Added by User</td>
                <td>{report.added_opening_count}</td>
              </tr>
              <tr>
                <td>Total Aperture Area</td>
                <td>{report.opening_area_mm2.toFixed(2)} mm²</td>
              </tr>
              <tr>
                <td>Sheet Dimensions</td>
                <td>
                  {report.sheet_width_mm.toFixed(2)} × {report.sheet_height_mm.toFixed(2)} mm
                </td>
              </tr>
              <tr>
                <td>Thickness</td>
                <td>{report.thickness_mm.toFixed(2)} mm</td>
              </tr>
              <tr>
                <td>Mesh Vertices</td>
                <td>{report.vertex_count.toLocaleString()}</td>
              </tr>
              <tr>
                <td>Mesh Faces</td>
                <td>{report.face_count.toLocaleString()}</td>
              </tr>
              <tr>
                <td>Separate Bodies</td>
                <td>{report.body_count}</td>
              </tr>
              <tr>
                <td>Watertight</td>
                <td>
                  <span className={`watertight-badge ${report.watertight ? 'yes' : 'no'}`}>
                    {report.watertight ? '✓ Yes' : '✗ No'}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Volume</td>
                <td>{report.volume_mm3.toFixed(2)} mm³</td>
              </tr>
              {report.warnings && report.warnings.length > 0 && (
                <tr>
                  <td colSpan="2">
                    <div style={{ marginTop: '0.5rem' }}>
                      <strong style={{ color: '#f59e0b' }}>⚠️ Warnings:</strong>
                      <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem', color: '#f59e0b' }}>
                        {report.warnings.map((w, idx) => (
                          <li key={idx} style={{ marginBottom: '0.25rem' }}>
                            {w}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
