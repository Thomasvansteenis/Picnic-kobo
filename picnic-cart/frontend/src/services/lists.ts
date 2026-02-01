import api from './api'
import type { RecurringList } from '../types'

interface ListsResponse {
  lists: RecurringList[]
}

interface CreateListRequest {
  name: string
  description?: string
  frequency: 'weekly' | 'biweekly' | 'monthly' | 'custom'
  custom_days?: number
  items: Array<{
    product_id: string
    product_name: string
    default_quantity: number
    unit_quantity?: string
    image_url?: string
  }>
}

interface AddToCartResponse {
  added: number
  failed: number
  cart: unknown
}

export async function getRecurringLists(): Promise<ListsResponse> {
  const response = await api.get('/lists/recurring')
  return response.data
}

export async function getRecurringList(listId: string): Promise<RecurringList> {
  const response = await api.get(`/lists/recurring/${listId}`)
  return response.data
}

export async function createRecurringList(data: CreateListRequest): Promise<RecurringList> {
  const response = await api.post('/lists/recurring', data)
  return response.data
}

export async function updateRecurringList(
  listId: string,
  data: Partial<CreateListRequest>
): Promise<RecurringList> {
  const response = await api.put(`/lists/recurring/${listId}`, data)
  return response.data
}

export async function deleteRecurringList(listId: string): Promise<{ success: boolean }> {
  const response = await api.delete(`/lists/recurring/${listId}`)
  return response.data
}

export async function addListToCart(listId: string): Promise<AddToCartResponse> {
  const response = await api.post(`/lists/recurring/${listId}/add-to-cart`)
  return response.data
}

export async function getSuggestedLists(): Promise<{ suggestions: RecurringList[] }> {
  const response = await api.get('/lists/suggestions')
  return response.data
}
