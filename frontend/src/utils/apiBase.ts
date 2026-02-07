/**
 * Vercel 배포 시 같은 오리진 프록시 사용 → 카톡 인앱 브라우저 등에서 크로스 오리진 차단 회피.
 * 로컬/일반 브라우저는 VITE_API_URL 그대로 사용.
 */
const buildTimeApiUrl = typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL
  ? String(import.meta.env.VITE_API_URL).trim()
  : ''

function isVercelHost(): boolean {
  if (typeof window === 'undefined') return false
  const h = window.location?.hostname || ''
  return h.includes('vercel.app')
}

/** API 요청 시 사용할 base URL. Vercel이면 프록시 경로, 아니면 백엔드 URL */
export function getApiBaseUrl(): string {
  if (isVercelHost()) return '/api/proxy'
  return buildTimeApiUrl
}

/** 스트리밍 등 fetch()에 넣을 전체 base (끝에 / 없음) */
export function getApiBaseForFetch(): string {
  if (isVercelHost()) return '/api/proxy'
  return buildTimeApiUrl
}
