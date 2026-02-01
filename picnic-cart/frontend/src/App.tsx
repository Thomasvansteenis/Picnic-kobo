import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthGuard } from './components/auth/AuthGuard'
import { MainLayout } from './components/layout/MainLayout'
import { HomePage } from './pages/HomePage'
import { SearchPage } from './pages/SearchPage'
import { CartPage } from './pages/CartPage'
import { OrdersPage } from './pages/OrdersPage'
import { ListsPage } from './pages/ListsPage'
import { RecipesPage } from './pages/RecipesPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { SettingsPage } from './pages/SettingsPage'
import { useSettingsStore } from './stores/settingsStore'

function App() {
  const { uiMode } = useSettingsStore()

  // If e-reader mode, redirect to legacy Flask templates
  if (uiMode === 'ereader') {
    window.location.href = '/legacy'
    return null
  }

  return (
    <BrowserRouter>
      <AuthGuard>
        <MainLayout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/cart" element={<CartPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/lists" element={<ListsPage />} />
            <Route path="/recipes" element={<RecipesPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </MainLayout>
      </AuthGuard>
    </BrowserRouter>
  )
}

export default App
