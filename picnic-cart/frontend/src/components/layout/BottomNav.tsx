import { NavLink } from 'react-router-dom'
import { Home, Search, ShoppingCart, Package, User } from 'lucide-react'
import { useCartStore } from '@/stores/cartStore'
import { cn } from '@/utils/cn'

const navItems = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/search', icon: Search, label: 'Zoeken' },
  { to: '/cart', icon: ShoppingCart, label: 'Wagen', showBadge: true },
  { to: '/orders', icon: Package, label: 'Bestellen' },
  { to: '/settings', icon: User, label: 'Profiel' },
]

export function BottomNav() {
  const { cart } = useCartStore()
  const itemCount = cart?.total_count || 0

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-100 lg:hidden safe-bottom">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center justify-center flex-1 h-full',
                'text-xs font-medium transition-colors',
                isActive ? 'text-primary-600' : 'text-gray-500'
              )
            }
          >
            {({ isActive }) => (
              <>
                <div className="relative">
                  <item.icon
                    className={cn('w-5 h-5 mb-1', isActive && 'text-primary-600')}
                  />
                  {item.showBadge && itemCount > 0 && (
                    <span className="absolute -top-1 -right-2 flex items-center justify-center min-w-[16px] h-4 px-1 rounded-full bg-primary-500 text-white text-[10px] font-medium">
                      {itemCount > 99 ? '99+' : itemCount}
                    </span>
                  )}
                </div>
                <span>{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
