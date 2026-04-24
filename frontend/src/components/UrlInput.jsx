import { useState } from 'react'
import './UrlInput.css'

const SAMPLE_URLS = [
  'https://example.com',
  'https://en.wikipedia.org/wiki/Web_accessibility',
]

export default function UrlInput({ onSubmit, loading }) {
  const [url, setUrl] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (url.trim()) onSubmit(url.trim())
  }

  return (
    <form className="url-input" onSubmit={handleSubmit} aria-label="URL audit form">
      <div className="url-input-header">
        <label htmlFor="url-field" className="url-input-label">
          Enter a website URL
        </label>
        <div className="sample-urls">
          {SAMPLE_URLS.map((u) => (
            <button
              key={u}
              type="button"
              className="sample-btn"
              onClick={() => setUrl(u)}
            >
              {u.replace('https://', '')}
            </button>
          ))}
        </div>
      </div>

      <div className="url-field-wrapper">
        <span className="url-prefix" aria-hidden="true">URL</span>
        <input
          id="url-field"
          type="url"
          className="url-field"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://yourwebsite.com"
          aria-label="Website URL to audit"
          aria-describedby="url-hint"
          autoComplete="url"
          spellCheck={false}
        />
      </div>

      <p id="url-hint" className="input-hint">
        The page's HTML will be fetched and audited against WCAG 2.2. Works best on public pages —
        sites with login walls or bot protection may not be reachable.
      </p>

      <button
        type="submit"
        className="submit-btn"
        disabled={loading || !url.trim()}
        aria-busy={loading}
      >
        {loading ? 'Fetching & auditing...' : 'Audit Website'}
      </button>
    </form>
  )
}
