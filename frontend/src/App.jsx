import { useState } from 'react'
import CodeInput from './components/CodeInput.jsx'
import ImageInput from './components/ImageInput.jsx'
import UrlInput from './components/UrlInput.jsx'
import ViolationReport from './components/ViolationReport.jsx'
import CodeDiff from './components/CodeDiff.jsx'
import ScoreMetrics from './components/ScoreMetrics.jsx'
import Loader from './components/Loader.jsx'
import { auditHTML, auditImage, auditURL } from './api/accessai.js'
import './App.css'

const TABS = [
  { id: 'html', label: 'Paste HTML' },
  { id: 'image', label: 'Upload Screenshot' },
  { id: 'url', label: 'Audit URL' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('html')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleHTMLSubmit = async (html) => {
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const data = await auditHTML(html)
      setResult(data)
    } catch (e) {
      setError(e.message || 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  const handleImageSubmit = async (file) => {
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const data = await auditImage(file)
      setResult(data)
    } catch (e) {
      setError(e.message || 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  const handleURLSubmit = async (url) => {
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const data = await auditURL(url)
      setResult(data)
    } catch (e) {
      setError(e.message || 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">Skip to main content</a>

      <header className="app-header">
        <div className="header-content">
          <div className="logo-group">
            <span className="logo-icon" aria-hidden="true">
              <svg viewBox="0 0 32 32" width="32" height="32" fill="none">
                <rect width="32" height="32" rx="8" fill="var(--accent-teal)" opacity="0.15" />
                <path d="M8 20l6-8 4 5 3-3 5 6" stroke="var(--accent-teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <circle cx="24" cy="10" r="3" fill="var(--accent-teal)" />
              </svg>
            </span>
            <h1 className="app-title">
              WCAG <span className="title-accent">Compliance Auditor</span>
            </h1>
          </div>
          <p className="app-tagline">Automated Fix Generation · RAG + Groq LLaMA · WCAG 2.2</p>
        </div>
      </header>

      <main id="main-content" className="app-main">
        <section className="input-section" aria-label="Input section">
          <div className="tab-bar" role="tablist" aria-label="Input method">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-controls={`tab-panel-${tab.id}`}
                id={`tab-${tab.id}`}
                className={`tab-btn ${activeTab === tab.id ? 'tab-btn--active' : ''}`}
                onClick={() => {
                  setActiveTab(tab.id)
                  setResult(null)
                  setError('')
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="input-card">
            <div
              id="tab-panel-html"
              role="tabpanel"
              aria-labelledby="tab-html"
              hidden={activeTab !== 'html'}
            >
              <CodeInput onSubmit={handleHTMLSubmit} loading={loading} />
            </div>
            <div
              id="tab-panel-image"
              role="tabpanel"
              aria-labelledby="tab-image"
              hidden={activeTab !== 'image'}
            >
              <ImageInput onSubmit={handleImageSubmit} loading={loading} />
            </div>
            <div
              id="tab-panel-url"
              role="tabpanel"
              aria-labelledby="tab-url"
              hidden={activeTab !== 'url'}
            >
              <UrlInput onSubmit={handleURLSubmit} loading={loading} />
            </div>
          </div>
        </section>

        {loading && (
          <div className="loader-section" aria-live="polite" aria-atomic="true">
            <Loader
              message={
                activeTab === 'image'
                  ? 'Reconstructing HTML from screenshot...'
                  : activeTab === 'url'
                  ? 'Fetching page and running WCAG 2.2 audit...'
                  : 'Running WCAG 2.2 accessibility audit...'
              }
            />
          </div>
        )}

        {error && (
          <div className="error-banner" role="alert" aria-live="assertive">
            <strong>Audit Error:</strong> {error}
          </div>
        )}

        {result && !loading && (
          <div className="results-section" aria-label="Audit results" aria-live="polite">
            <div className="results-banner" role="status">
              <span className="results-banner-icon" aria-hidden="true">✓</span>
              Audit complete for{' '}
              <strong>
                {result.input_type === 'image'
                  ? 'uploaded screenshot'
                  : result.input_type === 'url'
                  ? result.source_url
                  : 'provided HTML'}
              </strong>
              {' '}— {result.violations.length} violation{result.violations.length !== 1 ? 's' : ''} found
            </div>

            <div className="results-grid">
              <div className="result-card">
                <ViolationReport
                  violations={result.violations}
                  explanations={result.explanations}
                />
              </div>

              <div className="result-card">
                <ScoreMetrics metrics={result.metrics} />
              </div>

              <div className="result-card result-card--full">
                <CodeDiff
                  originalHtml={result.original_html}
                  fixedHtml={result.fixed_html}
                />
              </div>
            </div>

            {result.retrieved_wcag_criteria?.length > 0 && (
              <details className="rag-details">
                <summary className="rag-summary">
                  Retrieved WCAG Knowledge ({result.retrieved_wcag_criteria.length} criteria)
                </summary>
                <ul className="rag-list" aria-label="Retrieved WCAG criteria">
                  {result.retrieved_wcag_criteria.map((item, i) => (
                    <li key={i} className="rag-item">
                      <strong>{item.criterion}</strong>
                      <span className="rag-score">
                        similarity: {item.similarity_score}
                      </span>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Built for Prompt Engineering — Northeastern University &middot;{' '}
          <span className="footer-stack">RAG · Groq LLaMA 3.3 · ChromaDB · FastAPI · React 18</span>
        </p>
      </footer>
    </div>
  )
}
