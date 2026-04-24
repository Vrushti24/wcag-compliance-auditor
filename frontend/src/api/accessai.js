const BASE_URL = '/audit'

export async function auditHTML(htmlCode) {
  const response = await fetch(`${BASE_URL}/html`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ html: htmlCode }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function auditImage(imageFile) {
  const formData = new FormData()
  formData.append('file', imageFile)
  const response = await fetch(`${BASE_URL}/image`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function auditURL(url) {
  const response = await fetch(`${BASE_URL}/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function getMetrics(auditId) {
  const response = await fetch(`/metrics/${auditId}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}
