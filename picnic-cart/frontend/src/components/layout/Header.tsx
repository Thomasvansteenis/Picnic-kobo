import { Link } from 'react-router-dom'
import { Menu, Search, ShoppingCart, User } from 'lucide-react'
import { useCartStore } from '@/stores/cartStore'
import { useUIStore } from '@/stores/uiStore'
import { cn } from '@/utils/cn'

export function Header() {
  const { cart } = useCartStore()
  const { toggleSidebar, setCartDrawerOpen } = useUIStore()
  const itemCount = cart?.total_count || 0

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-gray-100">
      <div className="flex items-center justify-between h-16 px-4 lg:px-6">
        {/* Left: Menu + Logo */}
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="p-2 -ml-2 rounded-lg hover:bg-gray-100 lg:hidden"
          >
            <Menu className="w-5 h-5 text-gray-600" />
          </button>

          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
              <ShoppingCart className="w-5 h-5 text-white" />
            </div>
            <span className="font-display font-bold text-xl text-gray-900 hidden sm:block">
              Picnic
            </span>
          </Link>
        </div>

        {/* Center: Search (desktop) */}
        <div className="hidden md:flex flex-1 max-w-xl mx-8">
          <Link
            to="/search"
            className="flex items-center gap-2 w-full px-4 py-2.5 bg-gray-50 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
          >
            <Search className="w-4 h-4" />
            <span className="text-sm">Zoek producten...</span>
          </Link>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Search (mobile) */}
          <Link
            to="/search"
            className="p-2 rounded-lg hover:bg-gray-100 md:hidden"
          >
            <Search className="w-5 h-5 text-gray-600" />
          </Link>

          {/* Cart */}
          <button
            onClick={() => setCartDrawerOpen(true)}
            className="relative p-2 rounded-lg hover:bg-gray-100"
          >
            <ShoppingCart className="w-5 h-5 text-gray-600" />
            {itemCount > 0 && (
              <span
                className={cn(
                  'absolute -top-0.5 -right-0.5 flex items-center justify-center',
                  'min-w-[18px] h-[18px] px-1 rounded-full',
                  'bg-primary-500 text-white text-xs font-medium'
                )}
              >
                {itemCount > 99 ? '99+' : itemCount}
              </span>
            )}
          </button>

          {/* Profile */}
          <Link to="/settings" className="p-2 rounded-lg hover:bg-gray-100">
            <User className="w-5 h-5 text-gray-600" />
          </Link>
        </div>
      </div>
    </header>
  )
}
