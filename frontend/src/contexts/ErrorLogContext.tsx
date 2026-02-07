import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getErrors, clearErrors, subscribe, type ErrorEntry } from '../utils/errorLog'

type ContextValue = {
  errors: ErrorEntry[]
  clear: () => void
  open: boolean
  setOpen: (v: boolean) => void
}

const ErrorLogContext = createContext<ContextValue | null>(null)

export function ErrorLogProvider({ children }: { children: React.ReactNode }) {
  const [errors, setErrors] = useState<ErrorEntry[]>(getErrors())
  const [open, setOpen] = useState(false)

  useEffect(() => {
    return subscribe(() => setErrors(getErrors()))
  }, [])

  const clear = useCallback(() => {
    clearErrors()
    setErrors([])
    setOpen(false)
  }, [])

  return (
    <ErrorLogContext.Provider value={{ errors, clear, open, setOpen }}>
      {children}
    </ErrorLogContext.Provider>
  )
}

export function useErrorLog() {
  const ctx = useContext(ErrorLogContext)
  if (!ctx) throw new Error('useErrorLog must be used within ErrorLogProvider')
  return ctx
}
