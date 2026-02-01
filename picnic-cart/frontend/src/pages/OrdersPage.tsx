import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Package, Search, Clock, Check, X } from 'lucide-react'
import { Input, Card, CardContent, Badge, Button, OrderCardSkeleton } from '@/components/ui'
import { getUpcomingOrders, getOrderHistory, searchOrders } from '@/services/orders'
import { cn } from '@/utils/cn'

type TabType = 'upcoming' | 'history'

export function OrdersPage() {
  const [activeTab, setActiveTab] = useState<TabType>('upcoming')
  const [searchQuery, setSearchQuery] = useState('')

  const { data: upcomingData, isLoading: upcomingLoading } = useQuery({
    queryKey: ['upcomingOrders'],
    queryFn: getUpcomingOrders,
  })

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['orderHistory'],
    queryFn: () => getOrderHistory(20),
  })

  const { data: searchData, isLoading: searchLoading } = useQuery({
    queryKey: ['orderSearch', searchQuery],
    queryFn: () => searchOrders(searchQuery, activeTab === 'upcoming' ? 'upcoming' : 'history'),
    enabled: searchQuery.length > 1,
  })

  const orders = activeTab === 'upcoming'
    ? upcomingData?.orders || []
    : historyData?.orders || []

  const isLoading = activeTab === 'upcoming' ? upcomingLoading : historyLoading

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('nl-NL', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
  }

  const formatTime = (start: string, end: string) => {
    const s = new Date(start).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
    const e = new Date(end).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
    return `${s} - ${e}`
  }

  const formatPrice = (cents: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100)
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CURRENT':
        return <Badge variant="primary"><Clock className="w-3 h-3 mr-1" />Gepland</Badge>
      case 'COMPLETED':
        return <Badge variant="success"><Check className="w-3 h-3 mr-1" />Bezorgd</Badge>
      case 'CANCELLED':
        return <Badge variant="danger"><X className="w-3 h-3 mr-1" />Geannuleerd</Badge>
      default:
        return <Badge variant="gray">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Bestellingen</h1>

      {/* Search */}
      <Input
        type="search"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Zoek in bestellingen (bijv. melk)..."
        leftIcon={<Search className="w-5 h-5" />}
      />

      {/* Search Results */}
      {searchQuery && searchData?.matches && searchData.matches.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h3 className="font-medium text-gray-900 mb-3">
              Gevonden in bestellingen
            </h3>
            <div className="space-y-2">
              {searchData.matches.map((match, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div>
                    <p className="font-medium text-gray-900">{match.productName}</p>
                    <p className="text-sm text-gray-500">
                      {match.quantity}x • {formatDate(match.deliveryDate)}
                    </p>
                  </div>
                  <Badge variant={match.deliveryStatus === 'CURRENT' ? 'primary' : 'gray'}>
                    {match.deliveryStatus === 'CURRENT' ? 'Gepland' : 'Bezorgd'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {(['upcoming', 'history'] as TabType[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-2 font-medium text-sm border-b-2 transition-colors',
              activeTab === tab
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            {tab === 'upcoming' ? 'Gepland' : 'Geschiedenis'}
          </button>
        ))}
      </div>

      {/* Orders List */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <OrderCardSkeleton key={i} />
          ))}
        </div>
      ) : orders.length === 0 ? (
        <div className="text-center py-12">
          <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">
            Geen {activeTab === 'upcoming' ? 'geplande' : 'eerdere'} bestellingen
          </h2>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order, index) => (
            <motion.div
              key={order.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {formatDate(order.delivery_date)}
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                        <Clock className="w-4 h-4" />
                        {formatTime(order.delivery_slot_start, order.delivery_slot_end)}
                      </div>
                    </div>
                    {getStatusBadge(order.status)}
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">
                      {order.total_items} producten
                    </span>
                    <span className="font-semibold text-gray-900">
                      {formatPrice(order.total_price)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
