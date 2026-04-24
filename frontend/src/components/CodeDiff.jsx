import { useState } from 'react'
import './CodeDiff.css'

function computeDiff(originalLines, fixedLines) {
  const result = []
  const maxLen = Math.max(originalLines.length, fixedLines.length)

  // Simple line-by-line diff using LCS concept — for display purposes
  let origIdx = 0
  let fixedIdx = 0

  while (origIdx < originalLines.length || fixedIdx < fixedLines.length) {
    const origLine = originalLines[origIdx]
    const fixedLine = fixedLines[fixedIdx]

    if (origIdx >= originalLines.length) {
      result.push({ type: 'added', origLine: null, fixedLine, fixedLineNo: fixedIdx + 1 })
      fixedIdx++
    } else if (fixedIdx >= fixedLines.length) {
      result.push({ type: 'removed', origLine, fixedLine: null, origLineNo: origIdx + 1 })
      origIdx++
    } else if (origLine === fixedLine) {
      result.push({ type: 'unchanged', origLine, fixedLine, origLineNo: origIdx + 1, fixedLineNo: fixedIdx + 1 })
      origIdx++
      fixedIdx++
    } else {
      // Check if it's a FIXED comment added (line only in fixed)
      if (fixedLine && fixedLine.trim().startsWith('<!--') && fixedLine.includes('FIXED:')) {
        result.push({ type: 'added', origLine: null, fixedLine, fixedLineNo: fixedIdx + 1 })
        fixedIdx++
      } else {
        result.push({ type: 'changed', origLine, fixedLine, origLineNo: origIdx + 1, fixedLineNo: fixedIdx + 1 })
        origIdx++
        fixedIdx++
      }
    }
  }
  return result
}

export default function CodeDiff({ originalHtml, fixedHtml }) {
  const [showOnlyChanges, setShowOnlyChanges] = useState(false)

  const originalLines = (originalHtml || '').split('\n')
  const fixedLines = (fixedHtml || '').split('\n')
  const diffResult = computeDiff(originalLines, fixedLines)

  const changesCount = diffResult.filter((d) => d.type !== 'unchanged').length

  const displayedDiff = showOnlyChanges
    ? diffResult.filter((d) => d.type !== 'unchanged')
    : diffResult

  return (
    <section className="code-diff" aria-labelledby="diff-heading">
      <div className="diff-header">
        <h2 id="diff-heading" className="section-title">Code Changes</h2>
        <div className="diff-controls">
          <span className="diff-stats" aria-label={`${changesCount} lines changed`}>
            {changesCount} change{changesCount !== 1 ? 's' : ''}
          </span>
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={showOnlyChanges}
              onChange={(e) => setShowOnlyChanges(e.target.checked)}
              aria-label="Show only changed lines"
            />
            Show only changes
          </label>
        </div>
      </div>

      <div className="diff-panes" aria-label="Code comparison">
        <div className="diff-pane diff-pane--original" aria-label="Original code">
          <div className="diff-pane-label">
            <span className="diff-pane-dot diff-pane-dot--removed" aria-hidden="true" />
            Original
          </div>
          <div className="diff-code" role="region" aria-label="Original HTML">
            {displayedDiff.map((row, i) => (
              <div
                key={i}
                className={`diff-line diff-line--orig ${
                  row.type === 'removed' || row.type === 'changed' ? 'diff-line--red' : ''
                } ${row.type === 'added' ? 'diff-line--empty' : ''}`}
                aria-label={
                  row.type === 'changed' ? 'Modified line' :
                  row.type === 'removed' ? 'Removed line' : undefined
                }
              >
                <span className="diff-line-no" aria-hidden="true">
                  {row.origLineNo || ''}
                </span>
                <span className="diff-line-marker" aria-hidden="true">
                  {row.type === 'removed' || row.type === 'changed' ? '−' : row.type === 'added' ? '' : ' '}
                </span>
                <code className="diff-line-content">{row.origLine ?? ''}</code>
              </div>
            ))}
          </div>
        </div>

        <div className="diff-pane diff-pane--fixed" aria-label="Fixed code">
          <div className="diff-pane-label">
            <span className="diff-pane-dot diff-pane-dot--added" aria-hidden="true" />
            Fixed
          </div>
          <div className="diff-code" role="region" aria-label="Fixed HTML">
            {displayedDiff.map((row, i) => (
              <div
                key={i}
                className={`diff-line diff-line--fixed ${
                  row.type === 'added' || row.type === 'changed' ? 'diff-line--green' : ''
                } ${row.type === 'removed' ? 'diff-line--empty' : ''}`}
                aria-label={
                  row.type === 'changed' ? 'Fixed line' :
                  row.type === 'added' ? 'Added line' : undefined
                }
              >
                <span className="diff-line-no" aria-hidden="true">
                  {row.fixedLineNo || ''}
                </span>
                <span className="diff-line-marker" aria-hidden="true">
                  {row.type === 'added' || row.type === 'changed' ? '+' : row.type === 'removed' ? '' : ' '}
                </span>
                <code className="diff-line-content">{row.fixedLine ?? ''}</code>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="diff-copy-section">
        <button
          className="copy-btn"
          onClick={() => navigator.clipboard.writeText(fixedHtml)}
          aria-label="Copy fixed HTML to clipboard"
        >
          Copy Fixed HTML
        </button>
      </div>
    </section>
  )
}
