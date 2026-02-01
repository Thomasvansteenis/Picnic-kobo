import { cn } from '@/utils/cn'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
}

export function Skeleton({
  className,
  variant = 'text',
  width,
  height,
  style,
  ...props
}: SkeletonProps) {
  const variants = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  }

  return (
    <div
      className={cn('skeleton', variants[variant], className)}
      style={{
        width: width,
        height: height || (variant === 'text' ? '1em' : undefined),
        ...style,
      }}
      {...props}
    />
  )
}

// Pre-built skeleton components
export function ProductCardSkeleton() {
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <Skeleton variant="rectangular" className="w-full h-32 mb-3" />
      <Skeleton className="w-3/4 h-4 mb-2" />
      <Skeleton className="w-1/2 h-4 mb-3" />
      <div className="flex justify-between items-center">
        <Skeleton className="w-16 h-5" />
        <Skeleton variant="rectangular" className="w-20 h-8" />
      </div>
    </div>
  )
}

export function CartItemSkeleton() {
  return (
    <div className="flex gap-4 p-4 border-b border-gray-100">
      <Skeleton variant="rectangular" className="w-16 h-16 flex-shrink-0" />
      <div className="flex-1">
        <Skeleton className="w-3/4 h-4 mb-2" />
        <Skeleton className="w-1/2 h-3 mb-2" />
        <Skeleton className="w-16 h-5" />
      </div>
      <Skeleton variant="rectangular" className="w-24 h-8" />
    </div>
  )
}

export function OrderCardSkeleton() {
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex justify-between mb-3">
        <Skeleton className="w-32 h-5" />
        <Skeleton className="w-20 h-5" />
      </div>
      <Skeleton className="w-full h-4 mb-2" />
      <Skeleton className="w-2/3 h-4" />
    </div>
  )
}
