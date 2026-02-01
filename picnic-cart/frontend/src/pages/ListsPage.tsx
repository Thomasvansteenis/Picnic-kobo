import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ListChecks, Plus, ShoppingCart, Sparkles, Trash2, Edit2 } from 'lucide-react'
import { Card, CardContent, Button, Badge, Modal } from '@/components/ui'
import { getRecurringLists, addListToCart, deleteRecurringList, getSuggestedLists } from '@/services/lists'
import { useUIStore } from '@/stores/uiStore'
import { useCartStore } from '@/stores/cartStore'

export function ListsPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const queryClient = useQueryClient()
  const { addToast } = useUIStore()
  const { fetchCart } = useCartStore()

  const { data: listsData, isLoading } = useQuery({
    queryKey: ['recurringLists'],
    queryFn: getRecurringLists,
  })

  const { data: suggestionsData } = useQuery({
    queryKey: ['suggestedLists'],
    queryFn: getSuggestedLists,
  })

  const addToCartMutation = useMutation({
    mutationFn: addListToCart,
    onSuccess: (data) => {
      addToast('success', `${data.added} producten toegevoegd aan wagen`)
      fetchCart()
    },
    onError: () => {
      addToast('error', 'Kon lijst niet toevoegen')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteRecurringList,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurringLists'] })
      addToast('success', 'Lijst verwijderd')
    },
  })

  const getFrequencyLabel = (freq: string, days?: number) => {
    switch (freq) {
      case 'weekly': return 'Wekelijks'
      case 'biweekly': return 'Tweewekelijks'
      case 'monthly': return 'Maandelijks'
      case 'custom': return `Elke ${days} dagen`
      default: return freq
    }
  }

  const lists = listsData?.lists || []
  const suggestions = suggestionsData?.suggestions || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Terugkerende lijsten</h1>
          <p className="text-gray-500">Beheer je vaste boodschappen</p>
        </div>
        <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="w-4 h-4" />
          Nieuwe lijst
        </Button>
      </div>

      {/* AI Suggestions */}
      {suggestions.length > 0 && (
        <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-100">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <h2 className="font-semibold text-gray-900">Slimme suggesties</h2>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Gebaseerd op je koopgedrag
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {suggestions.slice(0, 2).map((list) => (
                <div
                  key={list.id}
                  className="bg-white rounded-lg p-3 border border-purple-100"
                >
                  <h3 className="font-medium text-gray-900 mb-1">{list.name}</h3>
                  <p className="text-sm text-gray-500 mb-2">
                    {list.items.length} producten
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => addToCartMutation.mutate(list.id)}
                    isLoading={addToCartMutation.isPending}
                  >
                    <ShoppingCart className="w-4 h-4" />
                    Toevoegen
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lists */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-4 h-24" />
            </Card>
          ))}
        </div>
      ) : lists.length === 0 ? (
        <div className="text-center py-12">
          <ListChecks className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">
            Nog geen lijsten
          </h2>
          <p className="text-gray-500 mb-6">
            Maak een lijst voor je vaste boodschappen
          </p>
          <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="w-4 h-4" />
            Eerste lijst maken
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {lists.map((list, index) => (
            <motion.div
              key={list.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{list.name}</h3>
                      <Badge variant="gray" size="sm" className="mt-1">
                        {getFrequencyLabel(list.frequency, list.custom_days)}
                      </Badge>
                    </div>
                    {list.is_auto_generated && (
                      <Sparkles className="w-4 h-4 text-purple-500" />
                    )}
                  </div>

                  <p className="text-sm text-gray-500 mb-4">
                    {list.items.length} producten
                  </p>

                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      className="flex-1"
                      onClick={() => addToCartMutation.mutate(list.id)}
                      isLoading={addToCartMutation.isPending}
                    >
                      <ShoppingCart className="w-4 h-4" />
                      Toevoegen
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (confirm('Lijst verwijderen?')) {
                          deleteMutation.mutate(list.id)
                        }
                      }}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Nieuwe lijst maken"
        size="lg"
      >
        <div className="p-6">
          <p className="text-gray-500 text-center py-8">
            Lijsteditor komt binnenkort...
          </p>
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => setIsCreateModalOpen(false)}
          >
            Sluiten
          </Button>
        </div>
      </Modal>
    </div>
  )
}
