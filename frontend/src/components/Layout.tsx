import { Outlet, NavLink } from 'react-router-dom'
import { LayoutDashboard, PieChart, LineChart, Bot, AlertCircle, X } from 'lucide-react'
import clsx from 'clsx'
import { useErrorLog } from '../contexts/ErrorLogContext'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '대시보드' },
  { to: '/portfolio', icon: PieChart, label: '포트폴리오' },
  { to: '/analysis', icon: LineChart, label: '시황 분석' },
  { to: '/auto-trade', icon: Bot, label: '자동매매' },
]

export default function Layout() {
  const { errors, clear, open, setOpen } = useErrorLog()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">K</span>
              </div>
              <span className="font-bold text-xl text-gray-900">투자 시스템</span>
            </div>
            
            <div className="flex items-center gap-2">
            {errors.length > 0 && (
              <button
                type="button"
                onClick={() => setOpen(true)}
                className="flex items-center gap-1 px-2 py-1.5 rounded-lg bg-amber-100 text-amber-800 text-xs font-medium"
                title="에러 로그 보기 (모바일 F12 대체)"
              >
                <AlertCircle className="w-4 h-4" />
                <span>에러 로그 ({errors.length})</span>
              </button>
            )}
            <nav className="flex gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors whitespace-nowrap',
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    )
                  }
                >
                  <item.icon className="w-4 h-4 flex-shrink-0" />
                  <span className="hidden sm:inline">{item.label}</span>
                </NavLink>
              ))}
            </nav>
            </div>
          </div>
        </div>
      </header>

      {/* 에러 로그 모달 (모바일에서 탭해서 확인) */}
      {open && (
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center bg-black/40" onClick={() => setOpen(false)}>
          <div className="bg-white rounded-t-2xl sm:rounded-xl shadow-xl max-h-[70vh] w-full max-w-lg flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="font-semibold text-gray-900">에러 로그 (F12 대체)</h3>
              <button type="button" onClick={() => setOpen(false)} className="p-1 rounded hover:bg-gray-100">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="overflow-auto p-4 space-y-3 flex-1">
              {errors.length === 0 ? (
                <p className="text-sm text-gray-500">저장된 에러 없음</p>
              ) : (
                errors.map((e, i) => (
                  <div key={i} className="text-xs rounded-lg bg-red-50 border border-red-100 p-3 space-y-1">
                    <div className="text-red-700 font-medium">{e.message}</div>
                    {e.url && <div className="text-gray-600 truncate">URL: {e.url}</div>}
                    {e.status != null && <div>상태: {e.status}</div>}
                    {e.detail && <div className="text-gray-500 break-all">{e.detail}</div>}
                    <div className="text-gray-400">{e.time}</div>
                  </div>
                ))
              )}
            </div>
            <div className="p-4 border-t">
              <button type="button" onClick={clear} className="w-full py-2 rounded-lg bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200">
                로그 비우기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
