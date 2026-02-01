import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, ShoppingCart, Calendar, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '@/components/ui'
import { getPurchaseFrequency, getSpendingAnalytics, getSuggestions, refreshAnalytics } from '@/services/analytics'
import { useUIStore } from '@/stores/uiStore'

export function AnalyticsPage() {
  const { addToast } = useUIStore()

  const { data: frequencyData, isLoading: freqLoading } = useQuery({
    queryKey: ['purchaseFrequency'],
    queryFn: () => getPurchaseFrequency(3),
  })

  const { data: spendingData, isLoading: spendLoading } = useQuery({
    queryKey: ['spendingAnalytics'],
    queryFn: () => getSpendingAnalytics(6),
  })

  const { data: suggestionsData } = useQuery({
    queryKey: ['suggestions'],
    queryFn: getSuggestions,
  })

  const handleRefresh = async () => {
    try {
      const result = await refreshAnalytics()
      addToast('success', `${result.processed_orders} bestellingen verwerkt`)
    } catch {
      addToast('error', 'Kon analyse niet vernieuwen')
    }
  }

  const formatPrice = (cents: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100)
  }

  const getFrequencyLabel = (days: number) => {
    if (days <= 7) return 'Wekelijks'
    if (days <= 14) return 'Tweewekelijks'
    if (days <= 30) return 'Maandelijks'
    return `~${Math.round(days)} dagen`
  }

  const products = frequencyData?.products || []
  const monthly = spendingData?.monthly || []
  const dueForReorder = suggestionsData?.due_for_reorder || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inzichten</h1>
          <p className="text-gray-500">Ontdek je kooppatronen</p>
        </div>
        <Button variant="secondary" size="sm" onClick={handleRefresh}>
          <RefreshCw className="w-4 h-4" />
          Vernieuwen
        </Button>
      </div>

      {/* Due for Reorder */}
      {dueForReorder.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Calendar className="w-5 h-5 text-orange-500" />
                <h2 className="font-semibold text-gray-900">Tijd om bij te bestellen</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {dueForReorder.slice(0, 5).map((item, i) => (
                  <Badge key={i} variant="warning">
                    {item.product_name}
                    <span className="ml-1 opacity-75">
                      ({item.days_overdue}d over)
                    </span>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Purchase Frequency */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary-500" />
                Aankoopfrequentie
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              {freqLoading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-8 bg-gray-100 rounded animate-pulse" />
                  ))}
                </div>
              ) : products.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  Nog niet genoeg data
                </p>
              ) : (
                <div className="space-y-3">
                  {products.slice(0, 8).map((product, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate text-sm">
                          {product.product_name}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <div
                            className="h-2 bg-primary-500 rounded-full"
                            style={{
                              width: `${Math.min(100, (7 / product.avg_days_between) * 100)}%`,
                            }}
                          />
                          <span className="text-xs text-gray-500 flex-shrink-0">
                            {getFrequencyLabel(product.avg_days_between)}
                          </span>
                        </div>
                      </div>
                      <Badge variant="gray" size="sm">
                        {product.total_purchases}x
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Monthly Spending */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary-500" />
                Maandelijkse uitgaven
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              {spendLoading ? (
                <div className="space-y-3">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="h-8 bg-gray-100 rounded animate-pulse" />
                  ))}
                </div>
              ) : monthly.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  Nog niet genoeg data
                </p>
              ) : (
                <div className="space-y-3">
                  {monthly.map((month, i) => {
                    const maxSpent = Math.max(...monthly.map((m) => m.total_spent))
                    return (
                      <div key={i} className="flex items-center gap-3">
                        <span className="w-12 text-sm text-gray-500">
                          {new Date(month.month).toLocaleDateString('nl-NL', {
                            month: 'short',
                          })}
                        </span>
                        <div className="flex-1">
                          <div
                            className="h-6 bg-primary-500 rounded flex items-center justify-end px-2"
                            style={{
                              width: `${(month.total_spent / maxSpent) * 100}%`,
                            }}
                          >
                            <span className="text-xs text-white font-medium">
                              {formatPrice(month.total_spent)}
                            </span>
                          </div>
                        </div>
                        <span className="text-xs text-gray-400 w-16 text-right">
                          {month.order_count} orders
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Category Breakdown */}
      {spendingData?.categories && spendingData.categories.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShoppingCart className="w-5 h-5 text-primary-500" />
                Uitgaven per categorie
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                {spendingData.categories.map((cat, i) => (
                  <div
                    key={i}
                    className="bg-gray-50 rounded-lg p-3 text-center"
                  >
                    <p className="font-medium text-gray-900">
                      {formatPrice(cat.total)}
                    </p>
                    <p className="text-sm text-gray-500">{cat.category}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
