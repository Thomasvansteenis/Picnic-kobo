// Product types
export interface Product {
  id: string
  name: string
  price: number
  display_price: string
  unit_quantity: string
  image_url?: string
  category?: string
  decorators?: Decorator[]
  inCart?: number
  inUpcomingOrder?: boolean
}

export interface Decorator {
  type: string
  quantity?: number
}

// Cart types
export interface CartItem {
  id: string
  product: Product
  quantity: number
  total_price: number
}

export interface Cart {
  items: CartItem[]
  total_price: number
  total_count: number
}

// Order types
export interface Order {
  id: string
  status: 'CURRENT' | 'COMPLETED' | 'CANCELLED'
  delivery_date: string
  delivery_slot_start: string
  delivery_slot_end: string
  total_price: number
  total_items: number
  items: OrderItem[]
}

export interface OrderItem {
  id: string
  product_id: string
  product_name: string
  quantity: number
  price: number
  image_url?: string
}

export interface OrderSearchMatch {
  deliveryId: string
  deliveryDate: string
  deliveryStatus: string
  productId: string
  productName: string
  quantity: number
  price: number
}

// Recurring list types
export interface RecurringList {
  id: string
  name: string
  description?: string
  frequency: 'weekly' | 'biweekly' | 'monthly' | 'custom'
  custom_days?: number
  is_active: boolean
  is_auto_generated: boolean
  items: RecurringListItem[]
  last_added_to_cart?: string
}

export interface RecurringListItem {
  id: string
  product_id: string
  product_name: string
  default_quantity: number
  unit_quantity?: string
  last_price?: number
  image_url?: string
}

// Recipe types
export interface ParsedIngredient {
  original_text: string
  quantity?: number
  unit?: string
  ingredient: string
  name?: string  // Alias for ingredient (used by backend)
  normalized: string
  search_term: string
}

export interface ProductMatchOption {
  id: string
  name: string
  price?: number
  image_url?: string
  unit_quantity?: string
  confidence: number
}

export interface ProductMatch {
  ingredient: ParsedIngredient
  matches: ProductMatchOption[]
  selected?: ProductMatchOption
  status: 'matched' | 'partial' | 'uncertain' | 'not_found'
  best_confidence: number
  needs_review: boolean
  suggested_quantity: number
}

export interface Recipe {
  id: string
  title?: string
  source_url?: string
  source_text?: string
  parsed_ingredients: ParsedIngredient[]
  matched_products: ProductMatch[]
  created_at: string
}

// Analytics types
export interface PurchaseFrequency {
  product_id: string
  product_name: string
  total_purchases: number
  avg_days_between: number
  last_purchased: string
  suggested_frequency: string
  confidence: number
}

export interface SpendingData {
  month: string
  total_spent: number
  order_count: number
  total_items: number
}

// Settings types
export interface Settings {
  ui_mode: 'full' | 'ereader'
  theme: 'light' | 'dark' | 'auto'
  language: string
  session_timeout_minutes: number
  show_product_images: boolean
  sound_enabled: boolean
}

// Auth types
export interface User {
  id: string
  display_name?: string
  picnic_user_id: string
}

export interface AuthState {
  isAuthenticated: boolean
  user: User | null
  needsPinSetup: boolean
}
