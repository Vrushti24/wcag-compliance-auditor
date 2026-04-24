import { useEffect, useState } from 'react'
import './ScoreMetrics.css'

const CIRCUMFERENCE = 2 * Math.PI * 44 // radius = 44

function ScoreRing({ score, label, color, animate }) {
  const [displayed, setDisplayed] = useState(0)

  useEffect(() => {
    if (!animate) { setDisplayed(score); return }
    let start = 0
    const step = score / 40
    const interval = setInterval(() => {
      start += step
      if (start >= score) { setDisplayed(score); clearInterval(interval) }
      else setDisplayed(Math.round(start))
    }, 20)
    return () => clearInterval(interval)
  }, [score, animate])

  const dashOffset = CIRCUMFERENCE - (displayed / 100) * CIRCUMFERENCE

  return (
    <div className="score-ring-container">
      <svg
        className="score-ring-svg"
        viewBox="0 0 100 100"
        width="140"
        height="140"
        role="img"
        aria-label={`${label}: ${score} out of 100`}
      >
        <circle cx="50" cy="50" r="44" className="score-ring-bg" />
        <circle
          cx="50"
          cy="50"
          r="44"
          className="score-ring-progress"
          style={{
            strokeDasharray: CIRCUMFERENCE,
            strokeDashoffset: dashOffset,
            stroke: color,
            transition: 'stroke-dashoffset 0.05s linear',
          }}
        />
        <text x="50" y="46" className="score-ring-value" style={{ fill: color }}>
          {displayed}
        </text>
        <text x="50" y="62" className="score-ring-unit">
          /100
        </text>
      </svg>
      <p className="score-ring-label">{label}</p>
    </div>
  )
}

export default function ScoreMetrics({ metrics }) {
  const { before, after, improvement } = metrics
  const [animate, setAnimate] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setAnimate(true), 300)
    return () => clearTimeout(t)
  }, [])

  return (
    <section className="score-metrics" aria-labelledby="metrics-heading">
      <h2 id="metrics-heading" className="section-title">Accessibility Score</h2>

      <div className="score-rings" aria-label="Before and after accessibility scores">
        <ScoreRing
          score={before.accessibility_score}
          label="Before"
          color="#ff4757"
          animate={animate}
        />
        <div className="score-arrow" aria-hidden="true">
          <svg viewBox="0 0 48 24" width="48" height="24">
            <path d="M0 12 L36 12 M28 4 L44 12 L28 20" stroke="var(--accent-teal)" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="score-improvement" aria-label={`Score improved by ${improvement.score_improvement} points`}>
            +{improvement.score_improvement}
          </span>
        </div>
        <ScoreRing
          score={after.accessibility_score}
          label="After"
          color="#00d4aa"
          animate={animate}
        />
      </div>

      <div className="metrics-grid" role="list" aria-label="Improvement metrics">
        <div className="metric-card" role="listitem">
          <span className="metric-value metric-value--teal" aria-label={`${improvement.violations_fixed} violations fixed`}>
            {improvement.violations_fixed}
          </span>
          <span className="metric-label">Violations Fixed</span>
        </div>

        <div className="metric-card" role="listitem">
          <span
            className={`metric-value ${improvement.violations_remaining > 0 ? 'metric-value--warn' : 'metric-value--teal'}`}
            aria-label={`${improvement.violations_remaining} remaining violations`}
          >
            {improvement.violations_remaining}
          </span>
          <span className="metric-label">Remaining</span>
        </div>

        <div className="metric-card" role="listitem">
          <span className="metric-value metric-value--teal" aria-label={`${improvement.fix_success_rate} percent fix success rate`}>
            {improvement.fix_success_rate}%
          </span>
          <span className="metric-label">Fix Success Rate</span>
        </div>

        <div className="metric-card" role="listitem">
          <span className="metric-value metric-value--teal" aria-label={`${after.wcag_pass_rate} percent WCAG pass rate after fixes`}>
            {after.wcag_pass_rate}%
          </span>
          <span className="metric-label">WCAG Pass Rate</span>
        </div>
      </div>

      <div className="eval-metrics" aria-labelledby="eval-heading">
        <h3 id="eval-heading" className="principles-heading">Evaluation Metrics</h3>
        <div className="eval-grid" role="list" aria-label="Proposal evaluation metrics">
          <div
            className={`eval-card ${improvement.fix_success_rate >= 90 ? 'eval-card--pass' : 'eval-card--warn'}`}
            role="listitem"
          >
            <span
              className="eval-value"
              aria-label={`Fix validity rate: ${improvement.fix_success_rate} percent`}
            >
              {improvement.fix_success_rate}%
            </span>
            <span className="eval-label">Fix Validity Rate</span>
            <span className="eval-target">Target ≥ 90%</span>
          </div>
          <div
            className={`eval-card ${after.wcag_pass_rate >= 85 ? 'eval-card--pass' : 'eval-card--warn'}`}
            role="listitem"
          >
            <span
              className="eval-value"
              aria-label={`WCAG pass rate after fixes: ${after.wcag_pass_rate} percent`}
            >
              {after.wcag_pass_rate}%
            </span>
            <span className="eval-label">WCAG Pass Rate</span>
            <span className="eval-target">Target ≥ 85%</span>
          </div>
          <div className="eval-card eval-card--info" role="listitem">
            <span className="eval-value" aria-label="Silent failure rate requires human review">&lt; 5%</span>
            <span className="eval-label">Silent Failure Target</span>
            <span className="eval-target">Human screen-reader review</span>
          </div>
        </div>
      </div>

      <div className="principles-breakdown" aria-labelledby="principles-heading">
        <h3 id="principles-heading" className="principles-heading">Violations by Principle</h3>
        <div className="principles-grid" role="list">
          {Object.entries(before.violations_by_principle).map(([principle, count]) => {
            const afterCount = after.violations_by_principle[principle] || 0
            return (
              <div key={principle} className="principle-item" role="listitem">
                <div className="principle-name">{principle}</div>
                <div className="principle-bar-container" aria-label={`${principle}: ${count} before, ${afterCount} after`}>
                  <div
                    className="principle-bar principle-bar--before"
                    style={{ width: `${Math.min(count * 12, 100)}%` }}
                    aria-hidden="true"
                  />
                  <div
                    className="principle-bar principle-bar--after"
                    style={{ width: `${Math.min(afterCount * 12, 100)}%` }}
                    aria-hidden="true"
                  />
                </div>
                <div className="principle-counts">
                  <span className="principle-count principle-count--before">{count}</span>
                  <span className="principle-count principle-count--arrow">→</span>
                  <span className="principle-count principle-count--after">{afterCount}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
