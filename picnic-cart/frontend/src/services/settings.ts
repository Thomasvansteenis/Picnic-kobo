import api from './api'
import type { Settings } from '../types'

export async function getSettings(): Promise<Settings> {
  const response = await api.get('/settings')
  return response.data
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
  const response = await api.put('/settings', settings)
  return response.data.settings
}

export async function getMode(): Promise<{ mode: 'full' | 'ereader' }> {
  const response = await api.get('/settings/mode')
  return response.data
}

export async function setMode(mode: 'full' | 'ereader'): Promise<{ success: boolean; mode: string }> {
  const response = await api.put('/settings/mode', { mode })
  return response.data
}
