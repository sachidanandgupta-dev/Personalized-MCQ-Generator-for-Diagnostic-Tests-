const TOKEN_KEY = 'mcq_access_token'
const USER_KEY = 'mcq_auth_user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setAuthSession({ access_token, user_id, username }) {
  localStorage.setItem(TOKEN_KEY, access_token)
  localStorage.setItem(USER_KEY, JSON.stringify({ user_id, username }))
}

export function getAuthUser() {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}
