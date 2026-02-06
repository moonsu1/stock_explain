/**
 * 포트폴리오 직접 입력/연동 데이터 - localStorage 공통 키
 */
export const PORTFOLIO_STORAGE_KEY = 'portfolio_manual'

export interface SavedPortfolio {
  totalValue: number
  totalProfit: number
  profitPercent: number
  accountNo?: string
  totalDeposit?: number
}

export function getSavedPortfolio(): SavedPortfolio | null {
  try {
    const raw = localStorage.getItem(PORTFOLIO_STORAGE_KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as SavedPortfolio
    if (typeof data.totalValue !== 'number' || typeof data.totalProfit !== 'number') return null
    return {
      totalValue: data.totalValue,
      totalProfit: data.totalProfit,
      profitPercent: typeof data.profitPercent === 'number' ? data.profitPercent : 0,
      accountNo: data.accountNo,
      totalDeposit: data.totalDeposit,
    }
  } catch {
    return null
  }
}

export function setSavedPortfolio(data: SavedPortfolio): void {
  localStorage.setItem(PORTFOLIO_STORAGE_KEY, JSON.stringify(data))
}

export function clearSavedPortfolio(): void {
  localStorage.removeItem(PORTFOLIO_STORAGE_KEY)
}
