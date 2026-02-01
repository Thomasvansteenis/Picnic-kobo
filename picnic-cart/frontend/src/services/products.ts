import api from './api'
import type { Product } from '../types'

interface SearchResponse {
  query: string
  results: Product[]
  in_cart: Record<string, number>
  in_upcoming_order: Record<string, boolean>
}

export async function searchProducts(query: string, category?: string): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query })
  if (category) {
    params.append('category', category)
  }
  const response = await api.get(`/products/search?${params}`)
  return response.data
}

export async function getProduct(productId: string): Promise<Product> {
  const response = await api.get(`/products/${productId}`)
  return response.data
}

export async function getCategories(): Promise<{ categories: string[] }> {
  const response = await api.get('/categories')
  return response.data
}
