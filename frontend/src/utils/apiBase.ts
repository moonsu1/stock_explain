/**
 * Vercel 배포 시 같은 오리진 프록시 사용.
 * 로컬 개발(DEV) 시에는 빈 문자열 → 상대 경로로 Vite 프록시 사용.
 */
const buildTimeApiUrl = typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL
  ? String(import.meta.env.VITE_API_URL).trim()
  : ''

function isVercelHost(): boolean {
  if (typeof window === 'undefined') return false
  const h = window.location?.hostname || ''
  return h.includes('vercel.app')
}

function isDev(): boolean {
  return typeof import.meta !== 'undefined' && !!import.meta.env?.DEV
}

/** API 요청 시 사용할 base URL */
export function getApiBaseUrl(): string {
  if (isVercelHost()) return '/api/proxy'
  if (isDev()) return '' // 로컬: Vite 프록시
  return buildTimeApiUrl
}

/** 스트리밍 등 fetch()에 넣을 base (끝에 / 없음) */
export function getApiBaseForFetch(): string {
  if (isVercelHost()) return '/api/proxy'
  if (isDev()) return '' // 로컬: Vite 프록시
  return buildTimeApiUrl
}
