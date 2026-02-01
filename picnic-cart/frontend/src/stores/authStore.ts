import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'
import * as authApi from '../services/auth'

interface AuthStore {
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  needsPinSetup: boolean
  error: string | null

  checkAuth: () => Promise<void>
  setupPin: (pin: string) => Promise<boolean>
  verifyPin: (pin: string) => Promise<boolean>
  logout: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      needsPinSetup: false,
      error: null,

      checkAuth: async () => {
        set({ isLoading: true, error: null })
        try {
          const status = await authApi.getAuthStatus()
          set({
            isAuthenticated: status.authenticated,
            user: status.user || null,
            needsPinSetup: status.needs_pin_setup || false,
            isLoading: false,
          })
        } catch (error) {
          set({
            isAuthenticated: false,
            user: null,
            needsPinSetup: true,
            isLoading: false,
          })
        }
      },

      setupPin: async (pin: string) => {
        set({ isLoading: true, error: null })
        try {
          const result = await authApi.setupPin(pin)
          if (result.success) {
            set({
              isAuthenticated: true,
              needsPinSetup: false,
              isLoading: false,
            })
            return true
          }
          return false
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to set up PIN',
            isLoading: false,
          })
          return false
        }
      },

      verifyPin: async (pin: string) => {
        set({ isLoading: true, error: null })
        try {
          const result = await authApi.verifyPin(pin)
          if (result.valid) {
            set({
              isAuthenticated: true,
              user: result.user,
              isLoading: false,
            })
            return true
          }
          set({
            error: 'Invalid PIN',
            isLoading: false,
          })
          return false
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to verify PIN',
            isLoading: false,
          })
          return false
        }
      },

      logout: async () => {
        try {
          await authApi.logout()
        } finally {
          set({
            isAuthenticated: false,
            user: null,
          })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'picnic-auth',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    }
  )
)
