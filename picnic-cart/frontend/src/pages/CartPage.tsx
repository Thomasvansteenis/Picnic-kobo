import { motion } from 'framer-motion'
import { ShoppingCart, Minus, Plus, Trash2, Package } from 'lucide-react'
import { useCartStore } from '@/stores/cartStore'
import { useUIStore } from '@/stores/uiStore'
import { Button, Card, CardContent, CartItemSkeleton } from '@/components/ui'
import { cn } from '@/utils/cn'

export function CartPage() {
  const { cart, isLoading, addItem, removeItem, clearCart } = useCartStore()
  const { addToast } = useUIStore()

  const formatPrice = (cents: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100)
  }

  const handleClearCart = async () => {
    if (window.confirm('Weet je zeker dat je de winkelwagen wilt legen?')) {
      try {
        await clearCart()
        addToast('success', 'Winkelwagen geleegd')
      } catch {
        addToast('error', 'Kon winkelwagen niet legen')
      }
    }
  }

  if (isLoading && !cart) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">Winkelwagen</h1>
        {[...Array(3)].map((_, i) => (
          <CartItemSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <ShoppingCart className="w-10 h-10 text-gray-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Je winkelwagen is leeg
        </h2>
        <p className="text-gray-500 mb-6">
          Voeg producten toe om te beginnen
        </p>
        <Button variant="primary" as="a" href="/search">
          Producten zoeken
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Winkelwagen</h1>
          <p className="text-gray-500">{cart.total_count} producten</p>
        </div>
        <Button variant="ghost" size="sm" onClick={handleClearCart}>
          <Trash2 className="w-4 h-4 mr-1" />
          Leegmaken
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-3">
          {cart.items.map((item, index) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card>
                <CardContent className="p-4">
                  <div className="flex gap-4">
                    {/* Product Image */}
                    <div className="w-20 h-20 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden">
                      {item.product.image_url ? (
                        <img
                          src={item.product.image_url}
                          alt={item.product.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Package className="w-8 h-8 text-gray-300" />
                        </div>
                      )}
                    </div>

                    {/* Product Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">
                        {item.product.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {item.product.unit_quantity}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatPrice(item.product.price)} per stuk
                      </p>
                    </div>

                    {/* Price & Quantity */}
                    <div className="flex flex-col items-end justify-between">
                      <span className="font-semibold text-gray-900">
                        {formatPrice(item.total_price)}
                      </span>

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
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <Card className="sticky top-24">
            <CardContent className="p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Overzicht</h2>

              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-gray-600">
                  <span>Subtotaal ({cart.total_count} items)</span>
                  <span>{formatPrice(cart.total_price)}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Bezorging</span>
                  <span className="text-green-600">Gratis</span>
                </div>
                <div className="border-t border-gray-100 pt-3">
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Totaal</span>
                    <span>{formatPrice(cart.total_price)}</span>
                  </div>
                </div>
              </div>

              <Button variant="primary" size="lg" className="w-full">
                Afrekenen
              </Button>

              <p className="text-xs text-gray-400 text-center mt-4">
                Je bestelling wordt verwerkt via de Picnic app
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
