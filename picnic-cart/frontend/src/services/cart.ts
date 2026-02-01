import api from './api'
import type { Cart } from '../types'

interface CartResponse {
  success: boolean
  cart: Cart
}

interface BulkAddResponse {
  added: number
  failed: number
  results: Array<{ productId: string; success: boolean; error?: string }>
  cart: Cart
}

export async function getCart(): Promise<Cart> {
  const response = await api.get('/cart')
  return response.data
}

export async function addToCart(productId: string, quantity = 1): Promise<CartResponse> {
  const response = await api.post('/cart/items', {
    product_id: productId,
    quantity,
  })
  return response.data
}

export async function removeFromCart(productId: string, quantity?: number): Promise<CartResponse> {
  const url = quantity
    ? `/cart/items/${productId}?quantity=${quantity}`
    : `/cart/items/${productId}`
  const response = await api.delete(url)
  return response.data
}

export async function updateQuantity(productId: string, quantity: number): Promise<CartResponse> {
  const response = await api.patch(`/cart/items/${productId}`, { quantity })
  return response.data
}

export async function clearCart(): Promise<{ success: boolean }> {
  const response = await api.delete('/cart')
  return response.data
}

export async function bulkAddToCart(
  items: Array<{ productId: string; quantity: number }>
): Promise<BulkAddResponse> {
  const response = await api.post('/cart/bulk-add', { items })
  return response.data
}
