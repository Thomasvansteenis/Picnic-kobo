# Picnic Full-Featured Web App - Design & Architecture Plan

## Executive Summary

Transform the existing e-reader-optimized Picnic shopping cart into a full-featured, beautifully designed web application for laptop and mobile, while maintaining the simplified e-reader version as an option.

---

## Part 1: Design Philosophy (Inspired by Superlist)

### What Makes Superlist Great

Based on research, Superlist excels in these areas that we'll adapt for our grocery app:

1. **Delightful Micro-interactions**
   - Satisfying completion sounds/animations when tasks are done
   - Smooth, purposeful transitions between states
   - Subtle feedback on every interaction

2. **Clean Information Architecture**
   - Clear visual hierarchy
   - Thoughtful use of whitespace
   - Organized, scannable layouts

3. **Premium Visual Design**
   - Beautiful custom backgrounds/themes
   - Elegant typography choices
   - Consistent iconography
   - Playful but professional aesthetic (squiggly dividers, etc.)

4. **Seamless Task + Notes Integration**
   - Content and actions live together
   - Everything is interconnected
   - Flexible nesting/organization

5. **Speed & Responsiveness**
   - Instant feedback
   - Optimistic UI updates
   - Skeleton loading states

### Design Principles for Picnic App

| Principle | Implementation |
|-----------|----------------|
| **Delight in Details** | Satisfying animations when adding to cart, subtle haptic-like feedback, playful empty states |
| **Clarity First** | Clear product images, readable prices, obvious actions |
| **Speed Perception** | Optimistic updates, skeleton loaders, instant search |
| **Personalization** | Custom themes, remember preferences, adapt to usage patterns |
| **Contextual Intelligence** | Smart suggestions, frequency insights, recipe parsing |

---

## Part 2: Feature Specifications

### Feature 1: Order History Analysis & Recurring Lists

**Purpose:** Analyze purchase patterns to help users never forget their staples.

**User Stories:**
- As a user, I want to see which products I buy most frequently
- As a user, I want to create "recurring lists" based on my buying patterns
- As a user, I want one-click addition of my recurring list to cart
- As a user, I want to set reminders for periodic purchases

**Technical Requirements:**
```
New MCP Tools Needed:
├── get_order_history()          # Fetch past orders (if Picnic API supports)
├── analyze_purchase_frequency() # Calculate frequency per product
└── get_suggested_recurring()    # AI-powered suggestions

Frontend Components:
├── FrequencyDashboard           # Visual chart of purchase patterns
├── RecurringListManager         # Create/edit/delete recurring lists
├── RecurringListCard            # Display a recurring list with quick-add
└── FrequencyBadge               # Show "You buy this every ~X days"
```

**Data Model:**
```typescript
interface RecurringList {
  id: string;
  name: string;                    // e.g., "Weekly Basics", "Monthly Stock"
  items: ProductReference[];
  frequency: 'weekly' | 'biweekly' | 'monthly' | 'custom';
  customDays?: number;
  lastAddedToCart?: Date;
  isAutoSuggest: boolean;          // true if AI-generated
}

interface PurchasePattern {
  productId: string;
  productName: string;
  avgDaysBetweenPurchases: number;
  totalPurchases: number;
  lastPurchased: Date;
  confidence: number;              // 0-1, how reliable the pattern is
}
```

**UI/UX Flow:**
1. Dashboard shows "Your Shopping Patterns" with visual frequency chart
2. System auto-suggests recurring lists based on patterns
3. User can create custom recurring lists
4. Quick "Add to Cart" button on each recurring list
5. Optional: Push notification/reminder when it's time to reorder

---

### Feature 2: Search Future Orders

**Purpose:** Quickly check if an item is already in upcoming delivery.

**User Stories:**
- As a user, I want to search if "milk" is in my upcoming order
- As a user, I want to see all items in my scheduled deliveries
- As a user, I want to add more of an item that's already ordered

**Technical Requirements:**
```
New MCP Tools Needed:
├── get_upcoming_orders()         # Fetch scheduled/upcoming deliveries
└── search_upcoming_orders(query) # Search within upcoming orders

Frontend Components:
├── UpcomingOrdersPanel           # List of scheduled deliveries
├── OrderSearchBar                # Search within orders
├── OrderItemCard                 # Display item in order with quantity
└── QuickAddMore                  # Add more of already-ordered item
```

**UI/UX Flow:**
1. Dedicated "Upcoming Orders" section in navigation
2. Search bar with instant filtering
3. Visual indicators: "Already ordered: 2x Milk in Tuesday's delivery"
4. When searching products, show badge if already in upcoming order

---

### Feature 3: Recipe/Ingredient Link Parser

**Purpose:** Paste a recipe URL or ingredient list and add items to cart.

**User Stories:**
- As a user, I want to paste a recipe URL and have ingredients extracted
- As a user, I want to paste a plain text ingredient list
- As a user, I want to match ingredients to Picnic products
- As a user, I want to review and adjust before adding to cart

**Technical Requirements:**
```
New Backend Service (or MCP Tool):
├── parse_recipe_url(url)         # Fetch & extract ingredients from URL
├── parse_ingredient_text(text)   # Parse plain text ingredients
├── match_ingredients_to_products(ingredients) # Find Picnic products
└── bulk_add_to_cart(items)       # Add multiple items at once

Frontend Components:
├── RecipeImportModal             # Modal for URL/text input
├── IngredientMatcher             # Show matched products with alternatives
├── IngredientCard                # Single ingredient with product match
├── BulkAddConfirmation           # Review before adding all
└── RecipeHistory                 # Recently imported recipes
```

**Ingredient Parsing Strategy:**
```typescript
interface ParsedIngredient {
  originalText: string;           // "2 cups all-purpose flour"
  quantity: number;               // 2
  unit: string;                   // "cups"
  ingredient: string;             // "all-purpose flour"
  normalized: string;             // "flour"
}

interface ProductMatch {
  ingredient: ParsedIngredient;
  matches: Array<{
    product: PicnicProduct;
    confidence: number;           // 0-1 match confidence
    quantityNeeded: number;       // How many to buy
  }>;
  status: 'matched' | 'partial' | 'not_found';
}
```

**UI/UX Flow:**
1. Click "Import Recipe" button
2. Paste URL or ingredient list
3. System parses and matches to Picnic products
4. User reviews matches, adjusts quantities, picks alternatives
5. One-click "Add All to Cart"

---

### Feature 4: Security Without Re-login

**Purpose:** Secure access without requiring Picnic credentials (already in MCP).

**User Stories:**
- As a user, I don't want to enter my Picnic credentials again
- As a user, I want only authorized access to my account
- As a user, I want secure session management

**Security Architecture:**
```
Option A: PIN/Password Protection
├── User sets a local PIN/password on first use
├── PIN stored as bcrypt hash in local storage/config
├── Session expires after X minutes of inactivity
└── Optional: Biometric on mobile (fingerprint/face)

Option B: Home Assistant Authentication
├── Leverage HA's built-in authentication
├── Only accessible when logged into HA
├── Use HA's user management
└── Ingress-based access control

Option C: Token-Based (Recommended)
├── Generate secure access token on first setup
├── Token stored in browser, validated by MCP server
├── Configurable expiration
├── Revokable from settings
└── Optional: IP restriction
```

**Recommended Approach: Hybrid**
1. Primary: Home Assistant ingress authentication (when accessed via HA)
2. Secondary: Local PIN for direct access
3. Session timeout after 30 minutes of inactivity
4. All API calls validated server-side

---

## Part 3: UI/UX Design System

### Color Palette

```css
/* Primary - Fresh Green (Picnic brand inspired) */
--primary-50: #f0fdf4;
--primary-100: #dcfce7;
--primary-500: #22c55e;
--primary-600: #16a34a;
--primary-700: #15803d;

/* Secondary - Warm Orange (for accents, CTAs) */
--secondary-500: #f97316;
--secondary-600: #ea580c;

/* Neutral - Clean grays */
--gray-50: #fafafa;
--gray-100: #f4f4f5;
--gray-200: #e4e4e7;
--gray-500: #71717a;
--gray-900: #18181b;

/* Semantic */
--success: #22c55e;
--warning: #eab308;
--error: #ef4444;
--info: #3b82f6;

/* Special - Superlist-inspired accents */
--accent-purple: #8b5cf6;
--accent-pink: #ec4899;
--accent-teal: #14b8a6;
```

### Typography

```css
/* Font Stack */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-display: 'Plus Jakarta Sans', var(--font-sans);

/* Scale */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */

/* Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing System

```css
/* 4px base unit */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### Component Design Tokens

```css
/* Border Radius */
--radius-sm: 0.375rem;   /* 6px - buttons, inputs */
--radius-md: 0.5rem;     /* 8px - cards */
--radius-lg: 0.75rem;    /* 12px - modals */
--radius-xl: 1rem;       /* 16px - large cards */
--radius-full: 9999px;   /* pills, avatars */

/* Shadows */
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
--shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
--shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1);

/* Transitions */
--transition-fast: 150ms ease;
--transition-base: 200ms ease;
--transition-slow: 300ms ease;
--transition-bounce: 500ms cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### Animation Principles

1. **Entry Animations**
   - Cards fade in + slide up (200ms)
   - Staggered delays for lists (50ms between items)
   - Scale from 0.95 to 1 for modals

2. **Micro-interactions**
   - Button press: scale to 0.98, subtle shadow change
   - Add to cart: item "flies" to cart icon
   - Quantity change: number animates up/down
   - Success: green checkmark with bounce

3. **Loading States**
   - Skeleton screens with shimmer effect
   - Optimistic updates (show change, then confirm)
   - Subtle pulsing for pending states

4. **Delightful Details**
   - Confetti on first order completion
   - Subtle sound on add-to-cart (optional, toggleable)
   - Easter egg animations (shake cart = items wiggle)

---

## Part 4: Responsive Layout System

### Breakpoints

```css
/* Mobile First */
--breakpoint-sm: 640px;   /* Large phones */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Laptops */
--breakpoint-xl: 1280px;  /* Desktops */
--breakpoint-2xl: 1536px; /* Large screens */
```

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER (sticky)                                            │
│  [Logo] [Search Bar] [Cart Icon] [Profile] [Mode Toggle]    │
├─────────────────────────────────────────────────────────────┤
│         │                                                   │
│  SIDE   │              MAIN CONTENT                         │
│  NAV    │                                                   │
│         │  ┌─────────────────────────────────────────────┐  │
│  • Home │  │                                             │  │
│  • Search│ │    Product Grid / Feature Panels            │  │
│  • Cart │  │                                             │  │
│  • Orders│ │                                             │  │
│  • Lists│  │                                             │  │
│  • Recipes│└─────────────────────────────────────────────┘  │
│  • Analytics│                                               │
│         │                                                   │
├─────────────────────────────────────────────────────────────┤
│  FOOTER (mobile: bottom nav bar)                            │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout (< 768px)

```
┌─────────────────────────┐
│  [≡] Logo    [🔍] [🛒]  │  ← Compact header
├─────────────────────────┤
│                         │
│    MAIN CONTENT         │
│    (full width)         │
│                         │
│                         │
├─────────────────────────┤
│ [🏠] [🔍] [🛒] [📋] [👤]│  ← Bottom nav bar
└─────────────────────────┘
```

### Mode Toggle: E-Reader vs Full Version

```
┌──────────────────────────────────┐
│  Experience Mode                 │
│  ┌─────────────┬────────────┐   │
│  │  E-Reader   │    Full    │   │
│  │  (Simple)   │  (Feature) │   │
│  └─────────────┴────────────┘   │
│                                  │
│  E-Reader mode:                  │
│  • High contrast                 │
│  • No animations                 │
│  • Large touch targets           │
│  • Basic cart & search only      │
└──────────────────────────────────┘
```

---

## Part 5: Page Designs

### 1. Home Dashboard

**Desktop:**
```
┌──────────────────────────────────────────────────────────┐
│  Good morning, Thomas! 👋                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐  ┌─────────────────────────────┐   │
│  │ UPCOMING ORDER  │  │  QUICK ADD                   │   │
│  │ Tuesday 14:00   │  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐│   │
│  │                 │  │  │Milk│ │Eggs│ │Bread│ │... ││   │
│  │ 12 items €47.50 │  │  └────┘ └────┘ └────┘ └────┘│   │
│  │ [View] [Edit]   │  │  Based on your buying habits │   │
│  └─────────────────┘  └─────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ YOUR RECURRING LISTS                                ││
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ││
│  │ │Weekly Basics │ │Monthly Stock │ │ + Create New │ ││
│  │ │ 8 items      │ │ 5 items      │ │              │ ││
│  │ │ [Add to Cart]│ │ [Add to Cart]│ │              │ ││
│  │ └──────────────┘ └──────────────┘ └──────────────┘ ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ IMPORT RECIPE                    🍳                  ││
│  │ Paste a recipe URL or ingredients to shop instantly ││
│  │ [Paste URL or text...]                      [Import]││
│  └─────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

### 2. Product Search

**Features:**
- Instant search with debouncing
- Category filters
- Grid/List view toggle
- "Already in cart" badges
- "Already ordered" badges
- Quick quantity adjustment

```
┌──────────────────────────────────────────────────────────┐
│  🔍 Search products...                    [Grid] [List]  │
├──────────────────────────────────────────────────────────┤
│  Categories: [All] [Dairy] [Bakery] [Produce] [Meat]    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  🖼️      │ │  🖼️      │ │  🖼️      │ │  🖼️      │   │
│  │ Whole    │ │ Semi     │ │ Oat      │ │ Almond   │   │
│  │ Milk 1L  │ │ Milk 1L  │ │ Milk 1L  │ │ Milk 1L  │   │
│  │ €1.29    │ │ €1.19    │ │ €2.49    │ │ €2.89    │   │
│  │ ⭐ Weekly│ │          │ │          │ │          │   │
│  │ [−] 2 [+]│ │ [+ Add]  │ │ [+ Add]  │ │ [+ Add]  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ✓ In cart    📦 Ordered                                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 3. Shopping Cart

**Features:**
- Grouped by category
- Easy quantity adjustment
- Running total
- Delivery slot selection
- Apply recurring list

```
┌──────────────────────────────────────────────────────────┐
│  🛒 Your Cart                              12 items      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  DAIRY (3)                                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 🖼️ Whole Milk 1L         €1.29    [−] 2 [+]   🗑️  │ │
│  │ 🖼️ Cheese Gouda 400g     €3.49    [−] 1 [+]   🗑️  │ │
│  │ 🖼️ Greek Yogurt 500g     €2.19    [−] 1 [+]   🗑️  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  BAKERY (2)                                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 🖼️ Whole Wheat Bread     €1.89    [−] 1 [+]   🗑️  │ │
│  │ 🖼️ Croissants 4-pack     €2.49    [−] 1 [+]   🗑️  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  Subtotal                                      €47.50   │
│  Delivery (Tue 14:00-15:00)                    €1.99   │
│  ─────────────────────────────────────────────────────  │
│  Total                                         €49.49   │
│                                                          │
│  [Change Delivery Time]              [Proceed to Order] │
└──────────────────────────────────────────────────────────┘
```

### 4. Analytics Dashboard

**Features:**
- Purchase frequency charts
- Spending trends
- Most bought items
- Suggested recurring lists

```
┌──────────────────────────────────────────────────────────┐
│  📊 Your Shopping Insights                               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ PURCHASE FREQUENCY                                   ││
│  │                                                      ││
│  │  Milk ████████████████████████ every 5 days         ││
│  │  Bread ██████████████████ every 7 days              ││
│  │  Eggs ████████████████ every 8 days                 ││
│  │  Cheese ██████████ every 14 days                    ││
│  │  Butter ████████ every 18 days                      ││
│  │                                                      ││
│  │  [Create Recurring List from These]                 ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  ┌────────────────────┐  ┌────────────────────────────┐ │
│  │ MONTHLY SPENDING   │  │ TOP CATEGORIES             │ │
│  │                    │  │                            │ │
│  │  Jan  ████ €180    │  │  🥛 Dairy       €45/mo    │ │
│  │  Feb  █████ €210   │  │  🍞 Bakery      €32/mo    │ │
│  │  Mar  ████ €195    │  │  🥬 Produce     €38/mo    │ │
│  │                    │  │  🥩 Meat        €52/mo    │ │
│  └────────────────────┘  └────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## Part 6: Technical Architecture

### Recommended Tech Stack Change

**Current:** Flask + Jinja2 (server-rendered, minimal interactivity)

**Proposed:** Keep Flask backend, add React frontend

```
┌─────────────────────────────────────────────────────────────┐
│                      ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Browser (React SPA)                                        │
│  ├── React 18 + TypeScript                                  │
│  ├── TailwindCSS + Framer Motion (animations)               │
│  ├── React Query (data fetching/caching)                    │
│  ├── Zustand (lightweight state management)                 │
│  └── React Router (navigation)                              │
│           │                                                 │
│           ▼ (REST API)                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Flask Backend (Enhanced)                            │   │
│  │  ├── /api/v2/* endpoints (JSON)                     │   │
│  │  ├── Recipe parsing service                         │   │
│  │  ├── Local data storage (recurring lists, etc.)     │   │
│  │  └── Session/token management                        │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                 │
│           ▼ (HTTP/JSON)                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  MCP Server (Extended)                               │   │
│  │  ├── Existing tools                                  │   │
│  │  ├── get_order_history()                             │   │
│  │  ├── get_upcoming_orders()                           │   │
│  │  └── Enhanced search                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Picnic API                                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure (Proposed)

```
picnic-webapp/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── ui/             # Base components (Button, Input, Card)
│   │   │   ├── layout/         # Layout components (Header, Sidebar)
│   │   │   ├── products/       # Product-related components
│   │   │   ├── cart/           # Cart components
│   │   │   ├── recipes/        # Recipe import components
│   │   │   └── analytics/      # Analytics/insights components
│   │   ├── pages/              # Page components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API service layer
│   │   ├── stores/             # Zustand stores
│   │   ├── types/              # TypeScript types
│   │   ├── utils/              # Utility functions
│   │   └── styles/             # Global styles, Tailwind config
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # Enhanced Flask backend
│   ├── app/
│   │   ├── api/                # API routes
│   │   │   ├── v2/             # New API version
│   │   │   └── legacy/         # Keep v1 for e-reader
│   │   ├── services/           # Business logic
│   │   │   ├── recipe_parser.py
│   │   │   ├── frequency_analyzer.py
│   │   │   └── recurring_lists.py
│   │   ├── models/             # Data models
│   │   └── utils/              # Utilities
│   ├── templates/              # Keep for e-reader version
│   └── requirements.txt
│
├── picnic-mcp-server/          # Enhanced MCP server
│   └── src/
│       └── index.ts            # Add new tools
│
└── docker-compose.yml          # Updated compose
```

### New API Endpoints

```yaml
# Cart & Products (keep existing, add new)
GET  /api/v2/cart
POST /api/v2/cart/items
DELETE /api/v2/cart/items/{id}
GET  /api/v2/products/search?q=

# Orders & Deliveries
GET  /api/v2/orders/upcoming
GET  /api/v2/orders/history
GET  /api/v2/orders/search?q=

# Recurring Lists
GET  /api/v2/lists/recurring
POST /api/v2/lists/recurring
PUT  /api/v2/lists/recurring/{id}
DELETE /api/v2/lists/recurring/{id}
POST /api/v2/lists/recurring/{id}/add-to-cart

# Analytics
GET  /api/v2/analytics/frequency
GET  /api/v2/analytics/spending
GET  /api/v2/analytics/suggestions

# Recipes
POST /api/v2/recipes/parse-url
POST /api/v2/recipes/parse-text
POST /api/v2/recipes/match-products
GET  /api/v2/recipes/history

# Auth & Settings
GET  /api/v2/auth/status
POST /api/v2/auth/verify-pin
GET  /api/v2/settings
PUT  /api/v2/settings
GET  /api/v2/settings/mode  # e-reader vs full
```

---

## Part 7: Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up React project with Vite + TypeScript
- [ ] Configure TailwindCSS and design system
- [ ] Create base UI components (Button, Input, Card, etc.)
- [ ] Set up React Query and API service layer
- [ ] Implement mode toggle (e-reader vs full)
- [ ] Build responsive layout shell

### Phase 2: Core Features (Week 3-4)
- [ ] Migrate search functionality to React
- [ ] Migrate cart functionality to React
- [ ] Implement product grid with images
- [ ] Add animations and micro-interactions
- [ ] Build mobile-responsive navigation

### Phase 3: New Features - Orders (Week 5-6)
- [ ] Extend MCP server with order history tools
- [ ] Build upcoming orders view
- [ ] Implement search within orders
- [ ] Add "already ordered" badges to search

### Phase 4: New Features - Analytics (Week 7-8)
- [ ] Build frequency analysis service
- [ ] Create analytics dashboard
- [ ] Implement recurring lists manager
- [ ] Add smart suggestions

### Phase 5: New Features - Recipes (Week 9-10)
- [ ] Build recipe URL parser (using cheerio/puppeteer)
- [ ] Implement ingredient text parser
- [ ] Create product matching algorithm
- [ ] Build recipe import UI

### Phase 6: Polish & Security (Week 11-12)
- [ ] Implement PIN/token security
- [ ] Add all micro-interactions and animations
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] Testing and bug fixes

---

## Part 8: Questions for You

Before we proceed to implementation, I'd like to clarify:

1. **Tech Stack Preference:**
   - Are you comfortable with React + TypeScript for the frontend?
   - Or would you prefer a different framework (Vue, Svelte, or staying with Flask+HTMX)?

2. **Data Persistence:**
   - Where should recurring lists and settings be stored?
     - Option A: Local file on server (simple)
     - Option B: SQLite database (more robust)
     - Option C: Home Assistant's storage

3. **Recipe Parsing:**
   - Should this use a third-party API (like Spoonacular)?
   - Or build custom parsing with AI (Claude API)?

4. **Order History:**
   - The Picnic API may have limits on order history access
   - Should we investigate API capabilities first?

5. **Mobile App:**
   - Is a PWA (Progressive Web App) sufficient?
   - Or do you eventually want a native app?

6. **Timeline:**
   - What's your priority order for the features?
   - Any hard deadlines?

---

## Sources

Design research based on:
- [Superlist Reviews on Product Hunt](https://www.producthunt.com/products/superlist/reviews)
- [TechRadar Superlist Review](https://www.techradar.com/pro/superlist-review)
- [60fps.design Superlist Animations](https://60fps.design/apps/superlist)
- [Efficient.app Superlist Review](https://efficient.app/apps/superlist)
- [The App Advocate - Superlist 2025](https://www.theappadvocate.com/superlist-2025-from-premium-to-do-app-to-ai-powered-productivity-powerhouse/)
