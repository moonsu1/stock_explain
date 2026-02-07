/**
 * Vercel serverless proxy: /api/proxy/* -> BACKEND_URL/api/*
 * 카톡 등 인앱 브라우저에서 크로스 오리진 차단 회피용.
 * Vercel 환경 변수에 BACKEND_URL (백엔드 주소) 설정 필요.
 */
const BACKEND_URL = process.env.BACKEND_URL || process.env.VITE_API_URL || ''

const FORWARD_HEADERS = ['content-type', 'accept', 'accept-language', 'authorization']

function getTargetUrl(pathSegments: string[], search: string): string {
  const base = BACKEND_URL.replace(/\/$/, '')
  const path = pathSegments.length ? '/' + pathSegments.join('/') : ''
  return `${base}${path}${search || ''}`
}

function forwardRequestHeaders(request: Request): Record<string, string> {
  const out: Record<string, string> = {}
  for (const name of FORWARD_HEADERS) {
    const v = request.headers.get(name)
    if (v) out[name] = v
  }
  return out
}

function responseHeaders(backendResponse: Response): Record<string, string> {
  const out: Record<string, string> = {}
  const copy = ['content-type', 'content-encoding', 'cache-control']
  for (const name of copy) {
    const v = backendResponse.headers.get(name)
    if (v) out[name] = v
  }
  return out
}

export const config = { runtime: 'nodejs' }

export default async function handler(request: Request): Promise<Response> {
  if (!BACKEND_URL) {
    return new Response(
      JSON.stringify({ error: 'BACKEND_URL not configured on Vercel' }),
      { status: 502, headers: { 'Content-Type': 'application/json' } }
    )
  }

  const url = new URL(request.url)
  const pathMatch = url.pathname.match(/^\/api\/proxy\/?(.*)$/i)
  const pathAfterProxy = pathMatch ? (pathMatch[1] || '') : ''
  const pathSegments = pathAfterProxy ? pathAfterProxy.split('/').filter(Boolean) : []
  const search = url.search || ''

  const targetUrl = getTargetUrl(pathSegments, search)
  const method = request.method
  const headers = forwardRequestHeaders(request)
  const body = method !== 'GET' && method !== 'HEAD' ? await request.arrayBuffer() : undefined

  try {
    const res = await fetch(targetUrl, { method, headers, body })
    const resHeaders = responseHeaders(res)
    return new Response(res.body, { status: res.status, headers: resHeaders })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return new Response(
      JSON.stringify({ error: 'Proxy fetch failed', detail: msg }),
      { status: 502, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
