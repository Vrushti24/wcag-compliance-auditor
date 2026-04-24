import './Loader.css'

export default function Loader({ message = 'Analyzing accessibility...' }) {
  return (
    <div className="loader-container" role="status" aria-live="polite">
      <div className="loader-ring">
        <div className="loader-ring-inner" />
      </div>
      <div className="loader-steps">
        <p className="loader-message">{message}</p>
        <div className="loader-step-list" aria-label="Processing steps">
          <span className="loader-step">Retrieving WCAG knowledge base</span>
          <span className="loader-step">Detecting violations</span>
          <span className="loader-step">Generating fixes</span>
          <span className="loader-step">Writing explanations</span>
        </div>
      </div>
    </div>
  )
}
