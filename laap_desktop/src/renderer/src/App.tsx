import React, { useState, useEffect } from 'react'
import Layout from './screens/Layout/Layout'
import Chat from './screens/Chat/Chat'
import Settings from './screens/Settings/Settings'
import Dashboard from './screens/Dashboard/Dashboard'
import { useSettingsStore } from './useSettingsStore'
import './styles/themes.css'

export type View = 'chat' | 'dashboard' | 'settings'

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('chat')
  const theme = useSettingsStore((s) => s.theme)

  // Apply theme on mount
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />
      case 'settings':
        return <Settings />
      case 'chat':
      default:
        return <Chat />
    }
  }

  return (
    <Layout currentView={currentView} onNavigate={setCurrentView}>
      {renderView()}
    </Layout>
  )
}

export default App
