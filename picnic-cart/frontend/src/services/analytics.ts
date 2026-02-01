import api from './api'
import type { PurchaseFrequency, SpendingData } from '../types'

interface FrequencyResponse {
  products: PurchaseFrequency[]
  generated_at: string
}

interface SpendingResponse {
  monthly: SpendingData[]
  categories: Array<{ category: string; total: number }>
  total: number
}

interface SuggestionsResponse {
  due_for_reorder: Array<{
    product_id: string
    product_name: string
    days_overdue: number
    avg_days_between: number
  }>
  frequently_bought_together: Array<{
    products: string[]
    frequency: number
  }>
}

export async function getPurchaseFrequency(
  minPurchases = 3
): Promise<FrequencyResponse> {
  const response = await api.get(`/analytics/frequency?min_purchases=${minPurchases}`)
  return response.data
}

export async function getSpendingAnalytics(
  months = 6
): Promise<SpendingResponse> {
  const response = await api.get(`/analytics/spending?months=${months}`)
  return response.data
}

export async function getSuggestions(): Promise<SuggestionsResponse> {
  const response = await api.get('/analytics/suggestions')
  return response.data
}

export async function refreshAnalytics(): Promise<{ success: boolean; processed_orders: number }> {
  const response = await api.post('/analytics/refresh')
  return response.data
}
