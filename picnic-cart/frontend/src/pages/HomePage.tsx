import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Search,
  Package,
  ChefHat,
  ListChecks,
  BarChart3,
  ArrowRight,
  Clock,
  ShoppingCart,
} from 'lucide-react'
import { Card, CardContent, Badge, Button } from '@/components/ui'
import { getUpcomingOrders } from '@/services/orders'
import { getRecurringLists } from '@/services/lists'
import { useCartStore } from '@/stores/cartStore'

const quickActions = [
  { to: '/search', icon: Search, label: 'Zoeken', color: 'bg-blue-500' },
  { to: '/orders', icon: Package, label: 'Bestellingen', color: 'bg-purple-500' },
  { to: '/recipes', icon: ChefHat, label: 'Recepten', color: 'bg-orange-500' },
  { to: '/lists', icon: ListChecks, label: 'Lijsten', color: 'bg-green-500' },
  { to: '/analytics', icon: BarChart3, label: 'Inzichten', color: 'bg-pink-500' },
]

export function HomePage() {
  const { cart } = useCartStore()

  const { data: upcomingOrders } = useQuery({
    queryKey: ['upcomingOrders'],
    queryFn: getUpcomingOrders,
  })

  const { data: recurringLists } = useQuery({
    queryKey: ['recurringLists'],
    queryFn: getRecurringLists,
  })

  const nextOrder = upcomingOrders?.orders?.[0]

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('nl-NL', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    })
  }

  const formatTime = (start: string, end: string) => {
    const startTime = new Date(start).toLocaleTimeString('nl-NL', {
      hour: '2-digit',
      minute: '2-digit',
    })
    const endTime = new Date(end).toLocaleTimeString('nl-NL', {
      hour: '2-digit',
      minute: '2-digit',
    })
    return `${startTime} - ${endTime}`
  }

  const formatPrice = (cents: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100)
  }

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl font-bold text-gray-900">
          Goedendag! 👋
        </h1>
        <p className="text-gray-500 mt-1">
          Wat wil je vandaag doen?
        </p>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-3 sm:grid-cols-5 gap-3"
      >
        {quickActions.map((action) => (
          <Link
            key={action.to}
            to={action.to}
            className="flex flex-col items-center p-4 bg-white rounded-xl border border-gray-100 hover:shadow-md transition-shadow"
          >
            <div
              className={`w-12 h-12 ${action.color} rounded-xl flex items-center justify-center mb-2`}
            >
              <action.icon className="w-6 h-6 text-white" />
            </div>
            <span className="text-sm font-medium text-gray-700">
              {action.label}
            </span>
          </Link>
        ))}
      </motion.div>

      {/* Next Delivery */}
      {nextOrder && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="primary">Volgende bezorging</Badge>
                  </div>
                  <h3 className="font-semibold text-gray-900">
                    {formatDate(nextOrder.delivery_date)}
                  </h3>
                  <div className="flex items-center gap-2 text-gray-500 mt-1">
                    <Clock className="w-4 h-4" />
                    <span>
                      {formatTime(
                        nextOrder.delivery_slot_start,
                        nextOrder.delivery_slot_end
                      )}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    {nextOrder.total_items} producten •{' '}
                    {formatPrice(nextOrder.total_price)}
                  </p>
                </div>
                <Link to={`/orders/${nextOrder.id}`}>
                  <Button variant="ghost" size="sm">
                    Bekijk
                    <ArrowRight className="w-4 h-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Current Cart Summary */}
      {cart && cart.total_count > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <Card className="bg-primary-50 border-primary-100">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
                    <ShoppingCart className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      Winkelwagen
                    </h3>
                    <p className="text-sm text-gray-600">
                      {cart.total_count} producten •{' '}
                      {formatPrice(cart.total_price)}
                    </p>
                  </div>
                </div>
                <Link to="/cart">
                  <Button variant="primary" size="sm">
                    Bekijken
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Recurring Lists */}
      {recurringLists?.lists && recurringLists.lists.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">
              Terugkerende lijsten
            </h2>
            <Link
              to="/lists"
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              Bekijk alle
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {recurringLists.lists.slice(0, 2).map((list) => (
              <Card key={list.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{list.name}</h3>
                      <p className="text-sm text-gray-500">
                        {list.items.length} producten
                      </p>
                    </div>
                    <Button variant="secondary" size="sm">
                      Toevoegen
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recipe Import CTA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-100">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <ChefHat className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">
                  Recept importeren
                </h3>
                <p className="text-sm text-gray-600">
                  Plak een recept-URL of ingrediëntenlijst
                </p>
              </div>
              <Link to="/recipes">
                <Button variant="secondary" size="sm">
                  Importeren
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
