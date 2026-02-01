import { create } from 'zustand'
import type { Cart } from '../types'
import * as cartApi from '../services/cart'

interface CartStore {
  cart: Cart | null
  isLoading: boolean
  error: string | null

  fetchCart: () => Promise<void>
  addItem: (productId: string, quantity?: number) => Promise<void>
  removeItem: (productId: string, quantity?: number) => Promise<void>
  updateQuantity: (productId: string, quantity: number) => Promise<void>
  clearCart: () => Promise<void>
  bulkAdd: (items: { productId: string; quantity: number }[]) => Promise<{ added: number; failed: number }>
}

export const useCartStore = create<CartStore>()((set, get) => ({
  cart: null,
  isLoading: false,
  error: null,

  fetchCart: async () => {
    set({ isLoading: true, error: null })
    try {
      const cart = await cartApi.getCart()
      set({ cart, isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load cart',
        isLoading: false,
      })
    }
  },

  addItem: async (productId, quantity = 1) => {
    const currentCart = get().cart

    // Optimistic update
    if (currentCart) {
      const existingItem = currentCart.items.find((item) => item.id === productId)
      if (existingItem) {
        set({
          cart: {
            ...currentCart,
            items: currentCart.items.map((item) =>
              item.id === productId
                ? { ...item, quantity: item.quantity + quantity }
                : item
            ),
            total_count: currentCart.total_count + quantity,
          },
        })
      }
    }

    try {
      const result = await cartApi.addToCart(productId, quantity)
      set({ cart: result.cart })
    } catch (error) {
      // Rollback on error
      set({ cart: currentCart })
      throw error
    }
  },

  removeItem: async (productId, quantity) => {
    const currentCart = get().cart

    try {
      const result = await cartApi.removeFromCart(productId, quantity)
      set({ cart: result.cart })
    } catch (error) {
      set({ cart: currentCart })
      throw error
    }
  },

  updateQuantity: async (productId, quantity) => {
    const currentCart = get().cart
    if (!currentCart) return

    const item = currentCart.items.find((i) => i.id === productId)
    if (!item) return

    const diff = quantity - item.quantity
    if (diff > 0) {
      await get().addItem(productId, diff)
    } else if (diff < 0) {
      await get().removeItem(productId, Math.abs(diff))
    }
  },

  clearCart: async () => {
    const currentCart = get().cart
    set({ cart: { items: [], total_price: 0, total_count: 0 } })

    try {
      await cartApi.clearCart()
    } catch (error) {
      set({ cart: currentCart })
      throw error
    }
  },

  bulkAdd: async (items) => {
    try {
      const result = await cartApi.bulkAddToCart(items)
      set({ cart: result.cart })
      return { added: result.added, failed: result.failed }
    } catch (error) {
      throw error
    }
  },
}))
