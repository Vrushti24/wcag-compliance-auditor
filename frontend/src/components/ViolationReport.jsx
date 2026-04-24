import { useState } from 'react'
import './ViolationReport.css'

const SEVERITY_LABELS = {
  critical: 'Critical',
  serious: 'Serious',
  moderate: 'Moderate',
  minor: 'Minor',
}

const PRINCIPLE_ICONS = {
  Perceivable: 'P',
  Operable: 'O',
  Understandable: 'U',
  Robust: 'R',
}

function ViolationCard({ violation, explanation }) {
  const [expanded, setExpanded] = useState(false)
  const sev = violation.severity?.toLowerCase() || 'minor'

  return (
    <article className={`violation-card severity-${sev}`} aria-label={`WCAG ${violation.violation_id} violation`}>
      <div className="violation-card-header">
        <div className="violation-badges">
          <span className={`severity-badge severity-badge--${sev}`} aria-label={`Severity: ${SEVERITY_LABELS[sev]}`}>
            {SEVERITY_LABELS[sev] || violation.severity}
          </span>
          <span className="wcag-id-badge" aria-label={`WCAG criterion ${violation.violation_id}`}>
            WCAG {violation.violation_id}
          </span>
          {violation.wcag_principle && (
            <span
              className="principle-badge"
              title={violation.wcag_principle}
              aria-label={`Principle: ${violation.wcag_principle}`}
            >
              {PRINCIPLE_ICONS[violation.wcag_principle] || '?'} {violation.wcag_principle}
            </span>
          )}
        </div>
        <button
          className="expand-btn"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
          aria-controls={`violation-details-${violation.violation_id}-${sev}`}
          aria-label={expanded ? 'Collapse details' : 'Expand details'}
        >
          {expanded ? '▲' : '▼'}
        </button>
      </div>

      <p className="violation-description">{violation.description}</p>

      {violation.element && (
        <code className="violation-element" aria-label="Offending HTML element">
          {violation.element}
        </code>
      )}

      {expanded && explanation && (
        <div
          id={`violation-details-${violation.violation_id}-${sev}`}
          className="violation-explanation"
          role="region"
          aria-label="Plain language explanation"
        >
          <h4 className="explanation-heading">Why this matters</h4>
          <p>{explanation.explanation}</p>
        </div>
      )}
    </article>
  )
}

export default function ViolationReport({ violations, explanations }) {
  const explanationMap = {}
  if (explanations) {
    for (const exp of explanations) {
      explanationMap[exp.violation_id] = exp
    }
  }

  const bySeverity = {
    critical: violations.filter((v) => v.severity === 'critical'),
    serious: violations.filter((v) => v.severity === 'serious'),
    moderate: violations.filter((v) => v.severity === 'moderate'),
    minor: violations.filter((v) => v.severity === 'minor'),
  }

  return (
    <section className="violation-report" aria-labelledby="violations-heading">
      <div className="violation-report-header">
        <h2 id="violations-heading" className="section-title">
          Violations Found
        </h2>
        <div className="violation-summary" role="status" aria-label="Violation summary">
          {Object.entries(bySeverity).map(([sev, items]) =>
            items.length > 0 ? (
              <span key={sev} className={`summary-chip summary-chip--${sev}`} aria-label={`${items.length} ${sev}`}>
                {items.length} {SEVERITY_LABELS[sev]}
              </span>
            ) : null
          )}
          {violations.length === 0 && (
            <span className="summary-chip summary-chip--pass">No violations found</span>
          )}
        </div>
      </div>

      {violations.length === 0 ? (
        <div className="no-violations" role="status">
          <div className="no-violations-icon" aria-hidden="true">✓</div>
          <p>Great news — no accessibility violations detected!</p>
        </div>
      ) : (
        <div className="violations-list" role="list" aria-label={`${violations.length} accessibility violations`}>
          {['critical', 'serious', 'moderate', 'minor'].map((sev) =>
            bySeverity[sev].map((v, i) => (
              <div key={`${v.violation_id}-${i}`} role="listitem">
                <ViolationCard
                  violation={v}
                  explanation={explanationMap[v.violation_id]}
                />
              </div>
            ))
          )}
        </div>
      )}
    </section>
  )
}
