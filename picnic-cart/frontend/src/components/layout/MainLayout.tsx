import { useEffect } from 'react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { BottomNav } from './BottomNav'
import { CartDrawer } from './CartDrawer'
import { ToastContainer } from '@/components/ui'
import { useCartStore } from '@/stores/cartStore'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const { fetchCart } = useCartStore()

  // Fetch cart on mount
  useEffect(() => {
    fetchCart()
  }, [fetchCart])

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <Sidebar />

      {/* Main Content */}
      <main className="lg:pl-64 pb-20 lg:pb-0">
        <div className="max-w-7xl mx-auto px-4 py-6 lg:px-8">
          {children}
        </div>
      </main>

      <BottomNav />
      <CartDrawer />
      <ToastContainer />
    </div>
  )
}
