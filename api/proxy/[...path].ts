/**
 * Vercel serverless proxy: /api/proxy/* -> BACKEND_URL/api/*
 * 카톡 등 인앱 브라우저에서 크로스 오리진 차단 회피용.
 * Vercel 환경 변수에 BACKEND_URL (백엔드 주소) 설정 필요.
 */
declare const process: { env: Record<string, string | undefined> }
const BACKEND_URL = process.env.BACKEND_URL || process.env.VITE_API_URL || ''

const FORWARD_HEADERS = ['content-type', 'accept', 'accept-language', 'authorization']

function getTargetUrl(pathSegments: string[], search: string): string {
  const base = BACKEND_URL.replace(/\/$/, '')
  const pathStr = pathSegments.length ? pathSegments.join('/') : ''
  const pathWithApi = pathStr.startsWith('api/') ? pathStr : pathStr ? `api/${pathStr}` : 'api'
  const path = '/' + pathWithApi
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

async function handleRequest(request: Request): Promise<Response> {
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
  const method = (request.method || 'GET').toUpperCase()
  const headers = forwardRequestHeaders(request)
  if (BACKEND_URL.includes('ngrok-free.app') || BACKEND_URL.includes('ngrok.io')) {
    headers['ngrok-skip-browser-warning'] = 'true'
    headers['User-Agent'] = headers['user-agent'] || 'Mozilla/5.0 (compatible; VercelProxy/1.0)'
  }
  const body = method !== 'GET' && method !== 'HEAD' ? await request.arrayBuffer() : undefined

  try {
    // redirect: 'manual' → ngrok이 302 주면 따라가며 POST가 GET으로 바뀌어 405 나는 것 방지
    const res = await fetch(targetUrl, {
      method,
      headers,
      body,
      redirect: BACKEND_URL.includes('ngrok') ? 'manual' : 'follow',
    })
    if (BACKEND_URL.includes('ngrok') && (res.status === 301 || res.status === 302)) {
      return new Response(
        JSON.stringify({
          error: 'ngrok redirect received. Ensure backend is running and ngrok tunnel is active.',
          hint: 'Restart ngrok and update BACKEND_URL if the URL changed.',
        }),
        { status: 502, headers: { 'Content-Type': 'application/json' } }
      )
    }
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

export default { fetch: handleRequest }
