/**
 * 앱 내 에러 로그 (모바일에서 F12 대신 확인용)
 */
const MAX = 20

export interface ErrorEntry {
  time: string
  message: string
  detail?: string
  url?: string
  status?: number
}

const list: ErrorEntry[] = []
const listeners: Set<() => void> = new Set()

function notify() {
  listeners.forEach((fn) => fn())
}

export function pushError(message: string, opts?: { url?: string; status?: number; detail?: string }) {
  const entry: ErrorEntry = {
    time: new Date().toLocaleTimeString('ko-KR'),
    message,
    ...opts,
  }
  list.unshift(entry)
  if (list.length > MAX) list.length = MAX
  notify()
}

export function getErrors(): ErrorEntry[] {
  return [...list]
}

export function clearErrors() {
  list.length = 0
  notify()
}

export function subscribe(fn: () => void): () => void {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}
