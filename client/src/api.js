import { clearAuthSession, getToken } from './authStorage'

const API_BASE =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') ||
  (import.meta.env.DEV ? 'http://localhost:8000' : '')

if (!API_BASE) {
  throw new Error(
    'VITE_API_URL is not set. Add it in Vercel → Settings → Environment Variables.',
  )
}

let onUnauthorized = null

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

async function request(path, options = {}, { auth = true } = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (auth) {
    const token = getToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401 && auth) {
    clearAuthSession()
    onUnauthorized?.()
  }

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ?? JSON.stringify(body)
    } catch {
      /* use statusText */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return response.json()
}

export function register(username, password) {
  return request(
    '/register',
    {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    },
    { auth: false },
  )
}

export function login(username, password) {
  return request(
    '/login',
    {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    },
    { auth: false },
  )
}

export function generateMcqs(educationalText) {
  return request('/generate-mcq', {
    method: 'POST',
    body: JSON.stringify({ educational_text: educationalText }),
  })
}

export function submitAnswer(questionId, isCorrect) {
  return request('/submit-answer', {
    method: 'POST',
    body: JSON.stringify({
      question_id: questionId,
      is_correct: isCorrect,
    }),
  })
}

export function fetchInsightAnalytics() {
  return request('/insight-analytics')
}

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  const headers = {}
  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}/upload-document`, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (response.status === 401) {
    clearAuthSession()
    onUnauthorized?.()
  }

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ?? JSON.stringify(body)
    } catch {
      /* use statusText */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return response.json()
}
