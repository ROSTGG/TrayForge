import React from 'react'

export default function Header() {
  return (
    <header className="header">
      <div className="header-title">
        🧬 Stencil Generator
        <span className="version-badge">v1.0</span>
      </div>
      <div className="header-links">
        <a href="https://github.com" target="_blank" rel="noopener noreferrer">
          GitHub
        </a>
      </div>
    </header>
  )
}
