import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, FileText, Search, Check, X, ShoppingCart, Loader2, ChevronDown, ChevronUp, AlertTriangle, CheckCircle } from 'lucide-react'
import { Card, CardContent, Button, Input, Badge } from '@/components/ui'
import { parseRecipeUrl, parseIngredientText, matchProductsToIngredients, addMatchedToCart } from '@/services/recipes'
import { useUIStore } from '@/stores/uiStore'
import { useCartStore } from '@/stores/cartStore'
import { cn } from '@/utils/cn'
import type { ProductMatch, ProductMatchOption } from '@/types'

type InputMode = 'url' | 'text'
type Step = 'input' | 'matching' | 'review'

// Confidence thresholds matching backend
const CONFIDENCE_HIGH = 0.7
const CONFIDENCE_MEDIUM = 0.4

function getConfidenceColor(confidence: number): string {
  if (confidence >= CONFIDENCE_HIGH) return 'text-green-600'
  if (confidence >= CONFIDENCE_MEDIUM) return 'text-yellow-600'
  return 'text-red-600'
}

function getConfidenceBg(confidence: number): string {
  if (confidence >= CONFIDENCE_HIGH) return 'bg-green-50 border-green-200'
  if (confidence >= CONFIDENCE_MEDIUM) return 'bg-yellow-50 border-yellow-200'
  return 'bg-red-50 border-red-200'
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= CONFIDENCE_HIGH) return 'Zeker'
  if (confidence >= CONFIDENCE_MEDIUM) return 'Controleer'
  return 'Onzeker'
}

function formatPrice(cents?: number): string {
  if (!cents) return ''
  return `€${(cents / 100).toFixed(2)}`
}

export function RecipesPage() {
  const [inputMode, setInputMode] = useState<InputMode>('url')
  const [step, setStep] = useState<Step>('input')
  const [urlInput, setUrlInput] = useState('')
  const [textInput, setTextInput] = useState('')
  const [recipeTitle, setRecipeTitle] = useState('')
  const [matches, setMatches] = useState<ProductMatch[]>([])
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)
  const [needsReviewCount, setNeedsReviewCount] = useState(0)

  const { addToast } = useUIStore()
  const { fetchCart } = useCartStore()

  const parseUrlMutation = useMutation({
    mutationFn: parseRecipeUrl,
    onSuccess: async (data) => {
      setRecipeTitle(data.title || 'Recept')
      setStep('matching')
      // Match products
      const matched = await matchProductsToIngredients(data.parsed_ingredients)

      // Auto-select best matches and track review count
      const processedMatches = matched.matches.map((m: ProductMatch) => ({
        ...m,
        selected: m.matches[0] // Auto-select first (best) match
      }))

      setMatches(processedMatches)
      setNeedsReviewCount(matched.needs_review_count || 0)
      setStep('review')

      // Auto-expand first uncertain match for review
      const firstUncertain = processedMatches.findIndex((m: ProductMatch) => m.needs_review)
      if (firstUncertain !== -1) {
        setExpandedIndex(firstUncertain)
      }
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

      const processedMatches = matched.matches.map((m: ProductMatch) => ({
        ...m,
        selected: m.matches[0]
      }))

      setMatches(processedMatches)
      setNeedsReviewCount(matched.needs_review_count || 0)
      setStep('review')

      const firstUncertain = processedMatches.findIndex((m: ProductMatch) => m.needs_review)
      if (firstUncertain !== -1) {
        setExpandedIndex(firstUncertain)
      }
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
    setExpandedIndex(null)
    setNeedsReviewCount(0)
  }

  const toggleSelection = (index: number) => {
    setMatches((prev) =>
      prev.map((m, i) =>
        i === index
          ? { ...m, selected: m.selected ? undefined : m.matches[0] }
          : m
      )
    )
  }

  const selectProduct = (matchIndex: number, product: ProductMatchOption) => {
    setMatches((prev) =>
      prev.map((m, i) =>
        i === matchIndex ? { ...m, selected: product } : m
      )
    )
    // Collapse after selection
    setExpandedIndex(null)
  }

  const toggleExpanded = (index: number, e: React.MouseEvent) => {
    e.stopPropagation()
    setExpandedIndex(expandedIndex === index ? null : index)
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

            {/* Review warning banner */}
            {needsReviewCount > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="flex items-center gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
              >
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-yellow-800">
                    {needsReviewCount} ingrediënt{needsReviewCount > 1 ? 'en' : ''} moet{needsReviewCount > 1 ? 'en' : ''} worden gecontroleerd
                  </p>
                  <p className="text-xs text-yellow-600">
                    Klik op gele/rode items om alternatieven te bekijken
                  </p>
                </div>
              </motion.div>
            )}

            <div className="space-y-2">
              {matches.map((match, index) => (
                <Card
                  key={index}
                  className={cn(
                    'transition-all duration-200 overflow-hidden',
                    match.selected ? 'border-primary-300' : 'border-gray-200',
                    match.needs_review && getConfidenceBg(match.best_confidence)
                  )}
                >
                  <CardContent className="p-0">
                    {/* Main row - clickable to toggle selection */}
                    <div
                      className={cn(
                        'p-3 cursor-pointer',
                        match.selected ? 'bg-primary-50' : ''
                      )}
                      onClick={() => toggleSelection(index)}
                    >
                      <div className="flex items-center gap-3">
                        {/* Selection checkbox */}
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

                        {/* Ingredient and product info */}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate">
                            {match.ingredient.original_text || match.ingredient.name}
                          </p>
                          {match.selected ? (
                            <div className="flex items-center gap-2">
                              <p className="text-sm text-primary-600 truncate">
                                → {match.selected.name}
                              </p>
                              {match.selected.price && (
                                <span className="text-xs text-gray-500">
                                  {formatPrice(match.selected.price)}
                                </span>
                              )}
                            </div>
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

                        {/* Confidence indicator and expand button */}
                        <div className="flex items-center gap-2">
                          {match.status !== 'not_found' && (
                            <>
                              {/* Confidence badge */}
                              <div className={cn(
                                'flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                                match.best_confidence >= CONFIDENCE_HIGH
                                  ? 'bg-green-100 text-green-700'
                                  : match.best_confidence >= CONFIDENCE_MEDIUM
                                    ? 'bg-yellow-100 text-yellow-700'
                                    : 'bg-red-100 text-red-700'
                              )}>
                                {match.best_confidence >= CONFIDENCE_HIGH ? (
                                  <CheckCircle className="w-3 h-3" />
                                ) : (
                                  <AlertTriangle className="w-3 h-3" />
                                )}
                                {Math.round(match.best_confidence * 100)}%
                              </div>

                              {/* Expand button for alternatives */}
                              {match.matches.length > 1 && (
                                <button
                                  onClick={(e) => toggleExpanded(index, e)}
                                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                                >
                                  {expandedIndex === index ? (
                                    <ChevronUp className="w-5 h-5 text-gray-400" />
                                  ) : (
                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                  )}
                                </button>
                              )}
                            </>
                          )}

                          {match.status === 'not_found' && (
                            <Badge variant="danger" size="sm">
                              <X className="w-3 h-3" />
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Expanded alternatives panel */}
                    <AnimatePresence>
                      {expandedIndex === index && match.matches.length > 0 && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="border-t border-gray-100 bg-gray-50"
                        >
                          <div className="p-2 space-y-1">
                            <p className="text-xs font-medium text-gray-500 px-2 py-1">
                              Kies een product:
                            </p>
                            {match.matches.map((product, pIndex) => (
                              <button
                                key={product.id}
                                onClick={() => selectProduct(index, product)}
                                className={cn(
                                  'w-full flex items-center gap-3 p-2 rounded-lg transition-colors text-left',
                                  match.selected?.id === product.id
                                    ? 'bg-primary-100 border border-primary-300'
                                    : 'hover:bg-white border border-transparent'
                                )}
                              >
                                {/* Product image placeholder */}
                                {product.image_url ? (
                                  <img
                                    src={product.image_url}
                                    alt={product.name}
                                    className="w-10 h-10 object-contain rounded bg-white"
                                  />
                                ) : (
                                  <div className="w-10 h-10 bg-gray-200 rounded flex items-center justify-center">
                                    <ShoppingCart className="w-4 h-4 text-gray-400" />
                                  </div>
                                )}

                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900 truncate">
                                    {product.name}
                                  </p>
                                  <div className="flex items-center gap-2">
                                    {product.unit_quantity && (
                                      <span className="text-xs text-gray-500">
                                        {product.unit_quantity}
                                      </span>
                                    )}
                                    <span className={cn(
                                      'text-xs',
                                      getConfidenceColor(product.confidence)
                                    )}>
                                      {Math.round(product.confidence * 100)}% match
                                    </span>
                                  </div>
                                </div>

                                <div className="text-right">
                                  {product.price && (
                                    <span className="text-sm font-medium text-gray-900">
                                      {formatPrice(product.price)}
                                    </span>
                                  )}
                                </div>

                                {match.selected?.id === product.id && (
                                  <Check className="w-5 h-5 text-primary-500 flex-shrink-0" />
                                )}
                              </button>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
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
