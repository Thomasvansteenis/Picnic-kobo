import api from './api'
import type { Order, OrderSearchMatch } from '../types'

interface OrdersResponse {
  orders: Order[]
  total?: number
  has_more?: boolean
}

interface OrderSearchResponse {
  query: string
  scope: string
  matches: OrderSearchMatch[]
}

export async function getUpcomingOrders(): Promise<OrdersResponse> {
  const response = await api.get('/orders/upcoming')
  return response.data
}

export async function getOrderHistory(
  limit = 50,
  offset = 0
): Promise<OrdersResponse> {
  const response = await api.get(`/orders/history?limit=${limit}&offset=${offset}`)
  return response.data
}

export async function getOrder(orderId: string): Promise<Order> {
  const response = await api.get(`/orders/${orderId}`)
  return response.data
}

export async function searchOrders(
  query: string,
  scope: 'upcoming' | 'history' | 'all' = 'all'
): Promise<OrderSearchResponse> {
  const response = await api.get(`/orders/search?q=${encodeURIComponent(query)}&scope=${scope}`)
  return response.data
}

export async function syncOrders(): Promise<{ synced: number; new_orders: number }> {
  const response = await api.post('/orders/sync')
  return response.data
}
