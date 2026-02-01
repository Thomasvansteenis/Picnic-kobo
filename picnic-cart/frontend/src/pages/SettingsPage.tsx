import { motion } from 'framer-motion'
import {
  Monitor,
  Smartphone,
  Moon,
  Sun,
  Volume2,
  VolumeX,
  Image,
  Clock,
  LogOut,
  ChevronRight,
} from 'lucide-react'
import { Card, CardContent, Badge } from '@/components/ui'
import { useSettingsStore } from '@/stores/settingsStore'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/utils/cn'

export function SettingsPage() {
  const settings = useSettingsStore()
  const { logout, user } = useAuthStore()

  const handleLogout = async () => {
    if (window.confirm('Weet je zeker dat je wilt uitloggen?')) {
      await logout()
    }
  }

  const settingGroups = [
    {
      title: 'Weergave',
      items: [
        {
          icon: settings.ui_mode === 'full' ? Monitor : Smartphone,
          label: 'Interface modus',
          description: settings.ui_mode === 'full' ? 'Volledige versie' : 'E-reader modus',
          action: (
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => settings.updateSettings({ ui_mode: 'full' })}
                className={cn(
                  'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                  settings.ui_mode === 'full'
                    ? 'bg-white shadow text-gray-900'
                    : 'text-gray-500'
                )}
              >
                Volledig
              </button>
              <button
                onClick={() => settings.updateSettings({ ui_mode: 'ereader' })}
                className={cn(
                  'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                  settings.ui_mode === 'ereader'
                    ? 'bg-white shadow text-gray-900'
                    : 'text-gray-500'
                )}
              >
                E-reader
              </button>
            </div>
          ),
        },
        {
          icon: settings.theme === 'dark' ? Moon : Sun,
          label: 'Thema',
          description: settings.theme === 'light' ? 'Licht' : settings.theme === 'dark' ? 'Donker' : 'Automatisch',
          action: (
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
              {(['light', 'dark', 'auto'] as const).map((theme) => (
                <button
                  key={theme}
                  onClick={() => settings.updateSettings({ theme })}
                  className={cn(
                    'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                    settings.theme === theme
                      ? 'bg-white shadow text-gray-900'
                      : 'text-gray-500'
                  )}
                >
                  {theme === 'light' ? 'Licht' : theme === 'dark' ? 'Donker' : 'Auto'}
                </button>
              ))}
            </div>
          ),
        },
        {
          icon: settings.show_product_images ? Image : Image,
          label: 'Product afbeeldingen',
          description: settings.show_product_images ? 'Aan' : 'Uit',
          action: (
            <button
              onClick={() =>
                settings.updateSettings({
                  show_product_images: !settings.show_product_images,
                })
              }
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.show_product_images ? 'bg-primary-500' : 'bg-gray-300'
              )}
            >
              <span
                className={cn(
                  'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                  settings.show_product_images ? 'left-7' : 'left-1'
                )}
              />
            </button>
          ),
        },
      ],
    },
    {
      title: 'Geluid & Notificaties',
      items: [
        {
          icon: settings.sound_enabled ? Volume2 : VolumeX,
          label: 'Geluiden',
          description: settings.sound_enabled ? 'Aan' : 'Uit',
          action: (
            <button
              onClick={() =>
                settings.updateSettings({ sound_enabled: !settings.sound_enabled })
              }
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.sound_enabled ? 'bg-primary-500' : 'bg-gray-300'
              )}
            >
              <span
                className={cn(
                  'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                  settings.sound_enabled ? 'left-7' : 'left-1'
                )}
              />
            </button>
          ),
        },
      ],
    },
    {
      title: 'Beveiliging',
      items: [
        {
          icon: Clock,
          label: 'Sessie timeout',
          description: `${settings.session_timeout_minutes} minuten`,
          action: (
            <select
              value={settings.session_timeout_minutes}
              onChange={(e) =>
                settings.updateSettings({
                  session_timeout_minutes: parseInt(e.target.value),
                })
              }
              className="bg-gray-100 rounded-lg px-3 py-1.5 text-sm"
            >
              <option value={15}>15 min</option>
              <option value={30}>30 min</option>
              <option value={60}>1 uur</option>
              <option value={120}>2 uur</option>
            </select>
          ),
        },
      ],
    },
  ]

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900">Instellingen</h1>

      {/* User Info */}
      {user && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-600 font-semibold text-lg">
                    {user.display_name?.charAt(0) || 'P'}
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {user.display_name || 'Picnic gebruiker'}
                  </h3>
                  <p className="text-sm text-gray-500">
                    Verbonden met Picnic
                  </p>
                </div>
                <Badge variant="success" className="ml-auto">
                  Actief
                </Badge>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Settings Groups */}
      {settingGroups.map((group, groupIndex) => (
        <motion.div
          key={group.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: groupIndex * 0.1 }}
        >
          <h2 className="text-sm font-medium text-gray-500 mb-2 px-1">
            {group.title}
          </h2>
          <Card>
            <CardContent className="p-0 divide-y divide-gray-100">
              {group.items.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                      <item.icon className="w-5 h-5 text-gray-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{item.label}</p>
                      <p className="text-sm text-gray-500">{item.description}</p>
                    </div>
                  </div>
                  {item.action}
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      ))}

      {/* Logout */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card>
          <CardContent className="p-0">
            <button
              onClick={handleLogout}
              className="flex items-center justify-between w-full p-4 text-left hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                  <LogOut className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="font-medium text-red-600">Uitloggen</p>
                  <p className="text-sm text-gray-500">
                    Sessie beëindigen
                  </p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </button>
          </CardContent>
        </Card>
      </motion.div>

      {/* Version */}
      <p className="text-center text-sm text-gray-400">
        Picnic Cart v4.0.0
      </p>
    </div>
  )
}
