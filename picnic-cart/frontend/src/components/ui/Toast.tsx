import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { cn } from '@/utils/cn'

export function ToastContainer() {
  const { toasts, removeToast } = useUIStore()

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100 }}
            transition={{ duration: 0.2 }}
            className={cn(
              'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg min-w-[300px]',
              toast.type === 'success' && 'bg-green-50 border border-green-200',
              toast.type === 'error' && 'bg-red-50 border border-red-200',
              toast.type === 'info' && 'bg-blue-50 border border-blue-200'
            )}
          >
            {toast.type === 'success' && (
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            )}
            {toast.type === 'error' && (
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            )}
            {toast.type === 'info' && (
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />
            )}

            <p
              className={cn(
                'flex-1 text-sm font-medium',
                toast.type === 'success' && 'text-green-800',
                toast.type === 'error' && 'text-red-800',
                toast.type === 'info' && 'text-blue-800'
              )}
            >
              {toast.message}
            </p>

            <button
              onClick={() => removeToast(toast.id)}
              className="p-1 rounded hover:bg-black/5 transition-colors"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
