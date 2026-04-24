import { useState, useRef } from 'react'
import './ImageInput.css'

const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
const ACCEPTED_EXTS = '.png,.jpg,.jpeg,.webp'

export default function ImageInput({ onSubmit, loading }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  const handleFile = (f) => {
    setError('')
    if (!f) return
    if (!ACCEPTED_TYPES.includes(f.type)) {
      setError(`Unsupported file type. Please upload PNG, JPG, or WEBP.`)
      return
    }
    if (f.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10MB.')
      return
    }
    setFile(f)
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    handleFile(dropped)
  }

  const handleChange = (e) => handleFile(e.target.files[0])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (file) onSubmit(file)
  }

  const clear = () => {
    setFile(null)
    setPreview(null)
    setError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <form className="image-input" onSubmit={handleSubmit} aria-label="Screenshot audit form">
      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''} ${preview ? 'has-preview' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        role="region"
        aria-label="File drop zone"
      >
        {preview ? (
          <div className="preview-container">
            <img src={preview} alt="Uploaded screenshot preview" className="preview-image" />
            <div className="preview-info">
              <span className="preview-name">{file.name}</span>
              <span className="preview-size">
                {(file.size / 1024).toFixed(1)} KB
              </span>
            </div>
          </div>
        ) : (
          <div className="drop-zone-content">
            <div className="drop-icon" aria-hidden="true">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <rect width="48" height="48" rx="12" fill="var(--bg-elevated)" />
                <path
                  d="M16 32h16M24 16v16M17 23l7-7 7 7"
                  stroke="var(--accent-teal)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <p className="drop-text">
              Drag and drop a webpage screenshot here
            </p>
            <p className="drop-subtext">or</p>
            <label className="file-label" htmlFor="screenshot-input">
              Browse files
              <input
                ref={inputRef}
                id="screenshot-input"
                type="file"
                accept={ACCEPTED_EXTS}
                onChange={handleChange}
                className="file-input-hidden"
                aria-describedby="file-hint"
              />
            </label>
            <p id="file-hint" className="drop-hint">Supported: PNG, JPG, WEBP — Max 10MB</p>
          </div>
        )}
      </div>

      {error && (
        <p className="image-error" role="alert" aria-live="assertive">
          <span aria-hidden="true">⚠ </span>{error}
        </p>
      )}

      <p className="image-input-description">
        Upload a screenshot of any webpage. LLaMA Vision will reconstruct the HTML structure, then audit it for WCAG 2.2 violations.
      </p>

      <div className="image-actions">
        {file && (
          <button type="button" className="clear-btn" onClick={clear} aria-label="Remove selected file">
            Remove file
          </button>
        )}
        <button
          type="submit"
          className="submit-btn"
          disabled={loading || !file}
          aria-busy={loading}
        >
          {loading ? 'Analyzing screenshot...' : 'Audit Screenshot'}
        </button>
      </div>
    </form>
  )
}
