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

function isLocalhostUrl(url: string): boolean {
  return /^https?:\/\/localhost(:\d+)?(\/|$)/i.test(url)
}

/** API 요청 시 사용할 base URL. Vercel이어도 VITE_API_URL이 localhost면 로컬 백엔드 사용 */
export function getApiBaseUrl(): string {
  if (isVercelHost() && buildTimeApiUrl && isLocalhostUrl(buildTimeApiUrl)) return buildTimeApiUrl
  if (isVercelHost()) return '/api/proxy'
  if (isDev()) return ''
  return buildTimeApiUrl
}

/** 스트리밍 등 fetch()에 넣을 base (끝에 / 없음) */
export function getApiBaseForFetch(): string {
  if (isVercelHost() && buildTimeApiUrl && isLocalhostUrl(buildTimeApiUrl)) return buildTimeApiUrl
  if (isVercelHost()) return '/api/proxy'
  if (isDev()) return ''
  return buildTimeApiUrl
}
