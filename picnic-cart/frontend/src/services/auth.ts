import api from './api'
import type { User } from '../types'

interface AuthStatus {
  authenticated: boolean
  user?: User
  needs_pin_setup?: boolean
  expires_at?: string
}

interface SetupPinResponse {
  success: boolean
  token?: string
}

interface VerifyPinResponse {
  valid: boolean
  token?: string
  user?: User
  expires_at?: string
}

export async function getAuthStatus(): Promise<AuthStatus> {
  const response = await api.get('/auth/status')
  return response.data
}

export async function setupPin(pin: string): Promise<SetupPinResponse> {
  const response = await api.post('/auth/setup-pin', { pin })
  if (response.data.token) {
    localStorage.setItem('picnic-token', response.data.token)
  }
  return response.data
}

export async function verifyPin(pin: string): Promise<VerifyPinResponse> {
  const response = await api.post('/auth/verify-pin', { pin })
  if (response.data.token) {
    localStorage.setItem('picnic-token', response.data.token)
  }
  return response.data
}

export async function logout(): Promise<void> {
  localStorage.removeItem('picnic-token')
  await api.post('/auth/logout')
}
