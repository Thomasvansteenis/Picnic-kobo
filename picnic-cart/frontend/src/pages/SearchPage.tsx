import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Grid, List, Package, ShoppingCart, Plus, Minus, Check } from 'lucide-react'
import { Input, Button, Badge, Card, ProductCardSkeleton } from '@/components/ui'
import { searchProducts } from '@/services/products'
import { useCartStore } from '@/stores/cartStore'
import { useUIStore } from '@/stores/uiStore'
import { cn } from '@/utils/cn'
import type { Product } from '@/types'

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [debouncedQuery, setDebouncedQuery] = useState(query)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const { cart, addItem, removeItem, isLoading: cartLoading } = useCartStore()
  const { addToast } = useUIStore()

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
      if (query) {
        setSearchParams({ q: query })
      } else {
        setSearchParams({})
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query, setSearchParams])

  const { data, isLoading, error } = useQuery({
    queryKey: ['products', debouncedQuery],
    queryFn: () => searchProducts(debouncedQuery),
    enabled: debouncedQuery.length > 0,
  })

  const getCartQuantity = (productId: string) => {
    return cart?.items.find((item) => item.id === productId)?.quantity || 0
  }

  const handleAddToCart = async (product: Product) => {
    try {
      await addItem(product.id)
      addToast('success', `${product.name} toegevoegd`)
    } catch {
      addToast('error', 'Kon product niet toevoegen')
    }
  }

  const formatPrice = (cents: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100)
  }

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="sticky top-16 z-30 -mx-4 px-4 py-3 bg-gray-50/95 backdrop-blur lg:-mx-8 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <Input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Zoek producten..."
              leftIcon={<Search className="w-5 h-5" />}
              autoFocus
            />
          </div>
          <div className="flex items-center gap-1 bg-white rounded-lg border border-gray-200 p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={cn(
                'p-2 rounded',
                viewMode === 'grid'
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              )}
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={cn(
                'p-2 rounded',
                viewMode === 'list'
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              )}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {!debouncedQuery ? (
        <div className="text-center py-12">
          <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">
            Zoek producten
          </h2>
          <p className="text-gray-500">
            Typ om te beginnen met zoeken
          </p>
        </div>
      ) : isLoading ? (
        <div
          className={cn(
            viewMode === 'grid'
              ? 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4'
              : 'space-y-3'
          )}
        >
          {[...Array(8)].map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-500">Er ging iets mis bij het zoeken</p>
        </div>
      ) : data?.results.length === 0 ? (
        <div className="text-center py-12">
          <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">
            Geen producten gevonden
          </h2>
          <p className="text-gray-500">
            Probeer een andere zoekterm
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-500">
            {data?.results.length} resultaten voor "{debouncedQuery}"
          </p>

          <div
            className={cn(
              viewMode === 'grid'
                ? 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4'
                : 'space-y-3'
            )}
          >
            <AnimatePresence mode="popLayout">
              {data?.results.map((product, index) => {
                const cartQty = getCartQuantity(product.id)
                const inUpcoming = data.in_upcoming_order?.[product.id]

                return (
                  <motion.div
                    key={product.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ delay: index * 0.02 }}
                  >
                    <Card
                      className={cn(
                        'overflow-hidden hover:shadow-md transition-shadow',
                        viewMode === 'list' && 'flex'
                      )}
                    >
                      {/* Product Image */}
                      <div
                        className={cn(
                          'bg-gray-100 flex items-center justify-center',
                          viewMode === 'grid' ? 'h-32' : 'w-20 h-20 flex-shrink-0'
                        )}
                      >
                        {product.image_url ? (
                          <img
                            src={product.image_url}
                            alt={product.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <ShoppingCart className="w-8 h-8 text-gray-300" />
                        )}
                      </div>

                      {/* Product Info */}
                      <div className="p-3 flex-1">
                        {/* Badges */}
                        <div className="flex gap-1 mb-1">
                          {cartQty > 0 && (
                            <Badge variant="primary" size="sm">
                              <Check className="w-3 h-3 mr-0.5" />
                              In wagen
                            </Badge>
                          )}
                          {inUpcoming && (
                            <Badge variant="secondary" size="sm">
                              <Package className="w-3 h-3 mr-0.5" />
                              Besteld
                            </Badge>
                          )}
                        </div>

                        <h3 className="font-medium text-gray-900 text-sm line-clamp-2 mb-1">
                          {product.name}
                        </h3>
                        <p className="text-xs text-gray-500 mb-2">
                          {product.unit_quantity}
                        </p>

                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-gray-900">
                            {formatPrice(product.price)}
                          </span>

                          {cartQty > 0 ? (
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => removeItem(product.id, 1)}
                                disabled={cartLoading}
                                className="w-7 h-7 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center disabled:opacity-50"
                              >
                                <Minus className="w-3 h-3" />
                              </button>
                              <span className="w-6 text-center text-sm font-medium">
                                {cartQty}
                              </span>
                              <button
                                onClick={() => handleAddToCart(product)}
                                disabled={cartLoading}
                                className="w-7 h-7 rounded-lg bg-primary-500 hover:bg-primary-600 flex items-center justify-center disabled:opacity-50"
                              >
                                <Plus className="w-3 h-3 text-white" />
                              </button>
                            </div>
                          ) : (
                            <Button
                              size="sm"
                              variant="primary"
                              onClick={() => handleAddToCart(product)}
                              disabled={cartLoading}
                            >
                              <Plus className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </Card>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        </>
      )}
    </div>
  )
}
