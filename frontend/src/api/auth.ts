const API_KEY_STORAGE_KEY = 'novel_api_key'

export function getStoredApiKey(): string {
  try {
    return sessionStorage.getItem(API_KEY_STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

export function setStoredApiKey(key: string): void {
  try {
    if (key) {
      sessionStorage.setItem(API_KEY_STORAGE_KEY, key)
    } else {
      sessionStorage.removeItem(API_KEY_STORAGE_KEY)
    }
  } catch {
    /* sessionStorage unavailable */
  }
}

export function authHeaders(): Record<string, string> {
  const apiKey = getStoredApiKey()
  return apiKey ? { 'X-API-Key': apiKey } : {}
}
