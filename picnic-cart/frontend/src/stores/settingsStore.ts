import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Settings } from '../types'

interface SettingsStore extends Settings {
  updateSettings: (settings: Partial<Settings>) => void
  toggleMode: () => void
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      ui_mode: 'full',
      theme: 'light',
      language: 'nl',
      session_timeout_minutes: 30,
      show_product_images: true,
      sound_enabled: false,

      updateSettings: (settings) => set((state) => ({ ...state, ...settings })),

      toggleMode: () => set((state) => ({
        ui_mode: state.ui_mode === 'full' ? 'ereader' : 'full',
      })),
    }),
    {
      name: 'picnic-settings',
    }
  )
)
