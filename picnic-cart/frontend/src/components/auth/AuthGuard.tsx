import { useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { PinSetup } from './PinSetup'
import { PinEntry } from './PinEntry'
import { Loader2, ShoppingCart } from 'lucide-react'

interface AuthGuardProps {
  children: React.ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading, needsPinSetup, checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-primary-500 rounded-2xl flex items-center justify-center mb-6">
          <ShoppingCart className="w-8 h-8 text-white" />
        </div>
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        <p className="mt-4 text-gray-500">Laden...</p>
      </div>
    )
  }

  // PIN setup needed
  if (needsPinSetup) {
    return <PinSetup />
  }

  // Not authenticated
  if (!isAuthenticated) {
    return <PinEntry />
  }

  // Authenticated
  return <>{children}</>
}
