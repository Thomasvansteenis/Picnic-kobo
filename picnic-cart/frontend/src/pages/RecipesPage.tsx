import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { ChefHat, Link, FileText, Search, Check, X, ShoppingCart, Loader2 } from 'lucide-react'
import { Card, CardContent, Button, Input, Badge, Modal } from '@/components/ui'
import { parseRecipeUrl, parseIngredientText, matchProductsToIngredients, addMatchedToCart } from '@/services/recipes'
import { useUIStore } from '@/stores/uiStore'
import { useCartStore } from '@/stores/cartStore'
import { cn } from '@/utils/cn'
import type { ParsedIngredient, ProductMatch } from '@/types'

type InputMode = 'url' | 'text'
type Step = 'input' | 'matching' | 'review'

export function RecipesPage() {
  const [inputMode, setInputMode] = useState<InputMode>('url')
  const [step, setStep] = useState<Step>('input')
  const [urlInput, setUrlInput] = useState('')
  const [textInput, setTextInput] = useState('')
  const [recipeTitle, setRecipeTitle] = useState('')
  const [matches, setMatches] = useState<ProductMatch[]>([])

  const { addToast } = useUIStore()
  const { fetchCart } = useCartStore()

  const parseUrlMutation = useMutation({
    mutationFn: parseRecipeUrl,
    onSuccess: async (data) => {
      setRecipeTitle(data.title || 'Recept')
      setStep('matching')
      // Match products
      const matched = await matchProductsToIngredients(data.parsed_ingredients)
      setMatches(matched.matches)
      setStep('review')
    },
    onError: () => {
      addToast('error', 'Kon recept niet laden')
    },
  })

  const parseTextMutation = useMutation({
    mutationFn: parseIngredientText,
    onSuccess: async (data) => {
      setRecipeTitle('Ingrediënten')
      setStep('matching')
      const matched = await matchProductsToIngredients(data.parsed_ingredients)
      setMatches(matched.matches)
      setStep('review')
    },
    onError: () => {
      addToast('error', 'Kon ingrediënten niet verwerken')
    },
  })

  const addToCartMutation = useMutation({
    mutationFn: addMatchedToCart,
    onSuccess: (data) => {
      addToast('success', `${data.added} producten toegevoegd`)
      fetchCart()
      resetForm()
    },
    onError: () => {
      addToast('error', 'Kon producten niet toevoegen')
    },
  })

  const handleSubmit = () => {
    if (inputMode === 'url' && urlInput) {
      parseUrlMutation.mutate(urlInput)
    } else if (inputMode === 'text' && textInput) {
      parseTextMutation.mutate(textInput)
    }
  }

  const resetForm = () => {
    setStep('input')
    setUrlInput('')
    setTextInput('')
    setRecipeTitle('')
    setMatches([])
  }

  const toggleMatch = (index: number) => {
    setMatches((prev) =>
      prev.map((m, i) =>
        i === index
          ? { ...m, selected: m.selected ? undefined : m.matches[0] }
          : m
      )
    )
  }

  const selectedMatches = matches.filter((m) => m.selected)
  const isLoading = parseUrlMutation.isPending || parseTextMutation.isPending

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Recept importeren</h1>
        <p className="text-gray-500">
          Plak een recept-URL of ingrediëntenlijst
        </p>
      </div>

      <AnimatePresence mode="wait">
        {step === 'input' && (
          <motion.div
            key="input"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {/* Input Mode Toggle */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setInputMode('url')}
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors',
                  inputMode === 'url'
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                <Link className="w-4 h-4" />
                URL
              </button>
              <button
                onClick={() => setInputMode('text')}
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors',
                  inputMode === 'text'
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                <FileText className="w-4 h-4" />
                Tekst
              </button>
            </div>

            <Card>
              <CardContent className="p-4">
                {inputMode === 'url' ? (
                  <Input
                    type="url"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://www.ah.nl/allerhande/recept/..."
                    leftIcon={<Link className="w-5 h-5" />}
                  />
                ) : (
                  <textarea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="2 eieren
500g bloem
1 liter melk
..."
                    className="w-full h-40 px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                  />
                )}

                <Button
                  variant="primary"
                  className="w-full mt-4"
                  onClick={handleSubmit}
                  disabled={inputMode === 'url' ? !urlInput : !textInput}
                  isLoading={isLoading}
                >
                  <Search className="w-4 h-4" />
                  Ingrediënten zoeken
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {step === 'matching' && (
          <motion.div
            key="matching"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <Loader2 className="w-12 h-12 text-primary-500 animate-spin mx-auto mb-4" />
            <h2 className="text-lg font-medium text-gray-900">
              Producten zoeken...
            </h2>
            <p className="text-gray-500">Even geduld</p>
          </motion.div>
        )}

        {step === 'review' && (
          <motion.div
            key="review"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {recipeTitle}
                </h2>
                <p className="text-sm text-gray-500">
                  {selectedMatches.length} van {matches.length} geselecteerd
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={resetForm}>
                Opnieuw
              </Button>
            </div>

            <div className="space-y-2">
              {matches.map((match, index) => (
                <Card
                  key={index}
                  className={cn(
                    'cursor-pointer transition-colors',
                    match.selected ? 'border-primary-300 bg-primary-50' : ''
                  )}
                  onClick={() => toggleMatch(index)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          'w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                          match.selected
                            ? 'border-primary-500 bg-primary-500'
                            : 'border-gray-300'
                        )}
                      >
                        {match.selected && (
                          <Check className="w-4 h-4 text-white" />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">
                          {match.ingredient.original_text}
                        </p>
                        {match.selected ? (
                          <p className="text-sm text-primary-600 truncate">
                            → {match.selected.name}
                          </p>
                        ) : match.status === 'not_found' ? (
                          <p className="text-sm text-red-500">
                            Niet gevonden
                          </p>
                        ) : (
                          <p className="text-sm text-gray-500">
                            {match.matches.length} opties
                          </p>
                        )}
                      </div>

                      {match.status === 'not_found' && (
                        <Badge variant="danger" size="sm">
                          <X className="w-3 h-3" />
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="sticky bottom-20 lg:bottom-4">
              <Button
                variant="primary"
                size="lg"
                className="w-full"
                disabled={selectedMatches.length === 0}
                onClick={() => addToCartMutation.mutate(selectedMatches)}
                isLoading={addToCartMutation.isPending}
              >
                <ShoppingCart className="w-5 h-5" />
                {selectedMatches.length} producten toevoegen
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
