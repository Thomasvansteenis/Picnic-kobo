import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ShoppingCart, Delete } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/utils/cn'

const PIN_LENGTH = 4

export function PinEntry() {
  const [pin, setPin] = useState('')
  const [isShaking, setIsShaking] = useState(false)
  const { verifyPin, isLoading, error, clearError } = useAuthStore()
  const inputRef = useRef<HTMLInputElement>(null)

  // Focus the hidden input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Auto-submit when PIN is complete
  useEffect(() => {
    if (pin.length === PIN_LENGTH) {
      handleSubmit()
    }
  }, [pin])

  const handleSubmit = async () => {
    if (pin.length < PIN_LENGTH) return

    const success = await verifyPin(pin)
    if (!success) {
      setIsShaking(true)
      setTimeout(() => {
        setIsShaking(false)
        setPin('')
      }, 500)
    }
  }

  const handleKeyPress = (digit: string) => {
    if (pin.length < PIN_LENGTH) {
      setPin((prev) => prev + digit)
      clearError()
    }
  }

  const handleDelete = () => {
    setPin((prev) => prev.slice(0, -1))
    clearError()
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, PIN_LENGTH)
    setPin(value)
    clearError()
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex flex-col items-center justify-center p-4">
      {/* Logo */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="flex flex-col items-center mb-8"
      >
        <div className="w-20 h-20 bg-primary-500 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-primary-500/30">
          <ShoppingCart className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Welkom terug</h1>
        <p className="text-gray-500 mt-1">Voer je PIN in</p>
      </motion.div>

      {/* Hidden input for keyboard support */}
      <input
        ref={inputRef}
        type="tel"
        inputMode="numeric"
        pattern="[0-9]*"
        maxLength={PIN_LENGTH}
        value={pin}
        onChange={handleInputChange}
        className="sr-only"
        autoFocus
      />

      {/* PIN dots */}
      <motion.div
        animate={isShaking ? { x: [0, -10, 10, -10, 10, 0] } : {}}
        transition={{ duration: 0.4 }}
        className="flex gap-4 mb-8"
      >
        {[...Array(PIN_LENGTH)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ scale: 0.8 }}
            animate={{
              scale: pin.length > i ? 1 : 0.8,
              backgroundColor: pin.length > i ? '#22c55e' : '#e5e7eb',
            }}
            className={cn(
              'w-4 h-4 rounded-full transition-colors',
              pin.length > i ? 'bg-primary-500' : 'bg-gray-300'
            )}
          />
        ))}
      </motion.div>

      {/* Error message */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-red-500 text-sm mb-4"
        >
          {error}
        </motion.p>
      )}

      {/* Loading indicator */}
      {isLoading && (
        <div className="mb-4">
          <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Numpad */}
      <div className="grid grid-cols-3 gap-3 max-w-xs">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((digit) => (
          <button
            key={digit}
            type="button"
            onClick={() => handleKeyPress(digit.toString())}
            disabled={isLoading}
            className={cn(
              'w-16 h-16 rounded-full text-2xl font-semibold',
              'bg-white border border-gray-200 shadow-sm',
              'hover:bg-gray-50 active:bg-gray-100 active:scale-95',
              'transition-all duration-150',
              'disabled:opacity-50'
            )}
          >
            {digit}
          </button>
        ))}
        <div /> {/* Empty space */}
        <button
          type="button"
          onClick={() => handleKeyPress('0')}
          disabled={isLoading}
          className={cn(
            'w-16 h-16 rounded-full text-2xl font-semibold',
            'bg-white border border-gray-200 shadow-sm',
            'hover:bg-gray-50 active:bg-gray-100 active:scale-95',
            'transition-all duration-150',
            'disabled:opacity-50'
          )}
        >
          0
        </button>
        <button
          type="button"
          onClick={handleDelete}
          disabled={isLoading || pin.length === 0}
          className={cn(
            'w-16 h-16 rounded-full flex items-center justify-center',
            'bg-white border border-gray-200 shadow-sm',
            'hover:bg-gray-50 active:bg-gray-100 active:scale-95',
            'transition-all duration-150',
            'disabled:opacity-50'
          )}
        >
          <Delete className="w-6 h-6 text-gray-600" />
        </button>
      </div>
    </div>
  )
}
