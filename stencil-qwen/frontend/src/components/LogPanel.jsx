import React from 'react'

export default function LogPanel({ logs }) {
  return (
    <div className="log-panel">
      {logs.length === 0 ? (
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
          Ready...
        </div>
      ) : (
        logs.map((log, idx) => (
          <div key={idx} className={`log-entry ${log.level}`}>
            <span className="log-timestamp">[{log.timestamp}]</span>
            <span>{log.message}</span>
          </div>
        ))
      )}
    </div>
  )
}
