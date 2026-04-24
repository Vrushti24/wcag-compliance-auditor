import { useState } from 'react'
import './CodeInput.css'

const SAMPLE_HTML = `<!DOCTYPE html>
<html>
<head><title>Sample Page</title></head>
<body>
  <img src="hero.jpg">
  <p style="color:#aaa; background:#fff">Welcome to our website</p>
  <input type="text" placeholder="Enter your name">
  <button></button>
  <a href="#">Click here</a>
  <h1>Main Title</h1>
  <h4>Subsection</h4>
</body>
</html>`

export default function CodeInput({ onSubmit, loading }) {
  const [html, setHtml] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (html.trim()) onSubmit(html)
  }

  const loadSample = () => setHtml(SAMPLE_HTML)

  return (
    <form className="code-input" onSubmit={handleSubmit} aria-label="HTML audit form">
      <div className="code-input-header">
        <label htmlFor="html-input" className="code-input-label">
          Paste your HTML code
        </label>
        <button
          type="button"
          className="sample-btn"
          onClick={loadSample}
          aria-label="Load sample HTML with accessibility violations"
        >
          Load sample with violations
        </button>
      </div>
      <textarea
        id="html-input"
        className="code-textarea"
        value={html}
        onChange={(e) => setHtml(e.target.value)}
        placeholder="<!DOCTYPE html>&#10;<html lang=&quot;en&quot;>&#10;  <head>...</head>&#10;  <body>...</body>&#10;</html>"
        rows={16}
        spellCheck={false}
        aria-label="HTML code to audit"
        aria-describedby="html-hint"
      />
      <p id="html-hint" className="input-hint">
        Paste any HTML snippet or full page. The AI will detect WCAG 2.2 violations and generate a fixed version.
      </p>
      <button
        type="submit"
        className="submit-btn"
        disabled={loading || !html.trim()}
        aria-busy={loading}
      >
        {loading ? 'Auditing...' : 'Run Accessibility Audit'}
      </button>
    </form>
  )
}
