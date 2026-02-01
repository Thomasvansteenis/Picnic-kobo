import { useState } from 'react'
import { ShoppingCart, Lock, Eye, EyeOff, Check } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { Button, Input, Card, CardContent } from '@/components/ui'
import { cn } from '@/utils/cn'

export function PinSetup() {
  const [pin, setPin] = useState('')
  const [confirmPin, setConfirmPin] = useState('')
  const [showPin, setShowPin] = useState(false)
  const [step, setStep] = useState<'enter' | 'confirm'>('enter')
  const { setupPin, isLoading, error, clearError } = useAuthStore()

  const handlePinChange = (value: string) => {
    // Only allow digits, max 6 characters
    const cleaned = value.replace(/\D/g, '').slice(0, 6)
    if (step === 'enter') {
      setPin(cleaned)
      clearError()
    } else {
      setConfirmPin(cleaned)
      clearError()
    }
  }

  const handleContinue = () => {
    if (pin.length >= 4) {
      setStep('confirm')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (pin !== confirmPin) {
      // This will be handled by the form validation
      return
    }

    await setupPin(pin)
  }

  const isValid = pin.length >= 4 && pin.length <= 6
  const pinsMatch = pin === confirmPin

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-8">
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 bg-primary-500 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-primary-500/30">
              <ShoppingCart className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Welkom bij Picnic</h1>
            <p className="text-gray-500 mt-2 text-center">
              {step === 'enter'
                ? 'Stel een PIN in om je account te beveiligen'
                : 'Bevestig je PIN'}
            </p>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center justify-center gap-2 mb-8">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                step === 'enter'
                  ? 'bg-primary-500 text-white'
                  : 'bg-primary-100 text-primary-600'
              )}
            >
              {step === 'confirm' ? <Check className="w-4 h-4" /> : '1'}
            </div>
            <div className="w-12 h-0.5 bg-gray-200" />
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                step === 'confirm'
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-200 text-gray-500'
              )}
            >
              2
            </div>
          </div>

          <form onSubmit={step === 'confirm' ? handleSubmit : (e) => { e.preventDefault(); handleContinue(); }}>
            <div className="space-y-4">
              <div className="relative">
                <Input
                  type={showPin ? 'text' : 'password'}
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  value={step === 'enter' ? pin : confirmPin}
                  onChange={(e) => handlePinChange(e.target.value)}
                  placeholder={step === 'enter' ? 'Voer PIN in (4-6 cijfers)' : 'Bevestig PIN'}
                  leftIcon={<Lock className="w-5 h-5" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPin(!showPin)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      {showPin ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  }
                  className="text-center text-2xl tracking-[0.5em] font-mono"
                  autoFocus
                />
              </div>

              {/* PIN strength indicator */}
              {step === 'enter' && pin.length > 0 && (
                <div className="flex gap-1">
                  {[...Array(6)].map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        'h-1 flex-1 rounded-full transition-colors',
                        i < pin.length ? 'bg-primary-500' : 'bg-gray-200'
                      )}
                    />
                  ))}
                </div>
              )}

              {/* Confirm PIN Match indicator */}
              {step === 'confirm' && confirmPin.length > 0 && (
                <p
                  className={cn(
                    'text-sm text-center',
                    pinsMatch ? 'text-green-600' : 'text-red-500'
                  )}
                >
                  {pinsMatch ? 'PINs komen overeen' : 'PINs komen niet overeen'}
                </p>
              )}

              {error && (
                <p className="text-sm text-red-500 text-center">{error}</p>
              )}

              {step === 'enter' ? (
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full"
                  disabled={!isValid}
                >
                  Doorgaan
                </Button>
              ) : (
                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="secondary"
                    size="lg"
                    className="flex-1"
                    onClick={() => {
                      setStep('enter')
                      setConfirmPin('')
                    }}
                  >
                    Terug
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    className="flex-1"
                    disabled={!pinsMatch}
                    isLoading={isLoading}
                  >
                    Bevestigen
                  </Button>
                </div>
              )}
            </div>
          </form>

          <p className="text-xs text-gray-400 text-center mt-6">
            Je PIN wordt veilig opgeslagen en is alleen lokaal toegankelijk.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
