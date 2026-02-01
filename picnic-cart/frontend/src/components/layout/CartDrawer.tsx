import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import { X, ShoppingCart, Minus, Plus, Trash2 } from 'lucide-react'
import { useCartStore } from '@/stores/cartStore'
import { useUIStore } from '@/stores/uiStore'
import { Button } from '@/components/ui'
import { cn } from '@/utils/cn'

export function CartDrawer() {
  const { cart, removeItem, addItem, isLoading } = useCartStore()
  const { isCartDrawerOpen, setCartDrawerOpen } = useUIStore()

  const formatPrice = (cents: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100)
  }

  return (
    <AnimatePresence>
      {isCartDrawerOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50"
            onClick={() => setCartDrawerOpen(false)}
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white shadow-xl flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between h-16 px-4 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <ShoppingCart className="w-5 h-5 text-gray-600" />
                <h2 className="font-semibold text-gray-900">
                  Winkelwagen
                  {cart && cart.total_count > 0 && (
                    <span className="text-gray-500 font-normal ml-1">
                      ({cart.total_count})
                    </span>
                  )}
                </h2>
              </div>
              <button
                onClick={() => setCartDrawerOpen(false)}
                className="p-2 rounded-lg hover:bg-gray-100"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {!cart || cart.items.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <ShoppingCart className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Je winkelwagen is leeg
                  </h3>
                  <p className="text-gray-500 mb-6">
                    Voeg producten toe om te beginnen
                  </p>
                  <Link
                    to="/search"
                    onClick={() => setCartDrawerOpen(false)}
                    className="inline-flex items-center justify-center gap-2 rounded-lg font-medium h-10 px-4 text-sm bg-primary-500 text-white hover:bg-primary-600"
                  >
                    Producten zoeken
                  </Link>
                </div>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {cart.items.map((item) => (
                    <li key={item.id} className="p-4">
                      <div className="flex gap-3">
                        {/* Product Image */}
                        <div className="w-16 h-16 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden">
                          {item.product.image_url ? (
                            <img
                              src={item.product.image_url}
                              alt={item.product.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-gray-400">
                              <ShoppingCart className="w-6 h-6" />
                            </div>
                          )}
                        </div>

                        {/* Product Info */}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-900 truncate">
                            {item.product.name}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {item.product.unit_quantity}
                          </p>
                          <p className="font-medium text-gray-900 mt-1">
                            {formatPrice(item.total_price)}
                          </p>
                        </div>

                        {/* Quantity Controls */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => removeItem(item.id, 1)}
                            disabled={isLoading}
                            className={cn(
                              'w-8 h-8 rounded-lg flex items-center justify-center',
                              'bg-gray-100 hover:bg-gray-200 transition-colors',
                              'disabled:opacity-50'
                            )}
                          >
                            {item.quantity === 1 ? (
                              <Trash2 className="w-4 h-4 text-red-500" />
                            ) : (
                              <Minus className="w-4 h-4 text-gray-600" />
                            )}
                          </button>
                          <span className="w-8 text-center font-medium">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => addItem(item.id, 1)}
                            disabled={isLoading}
                            className={cn(
                              'w-8 h-8 rounded-lg flex items-center justify-center',
                              'bg-primary-500 hover:bg-primary-600 transition-colors',
                              'disabled:opacity-50'
                            )}
                          >
                            <Plus className="w-4 h-4 text-white" />
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Footer */}
            {cart && cart.items.length > 0 && (
              <div className="border-t border-gray-100 p-4 space-y-4 bg-white safe-bottom">
                <div className="flex items-center justify-between text-lg font-semibold">
                  <span>Totaal</span>
                  <span>{formatPrice(cart.total_price)}</span>
                </div>
                <div className="flex gap-3">
                  <Button
                    variant="secondary"
                    className="flex-1"
                    onClick={() => setCartDrawerOpen(false)}
                  >
                    Verder winkelen
                  </Button>
                  <Link
                    to="/cart"
                    onClick={() => setCartDrawerOpen(false)}
                    className="flex-1"
                  >
                    <Button variant="primary" className="w-full">
                      Bekijk wagen
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
