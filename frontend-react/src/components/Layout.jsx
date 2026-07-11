import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, Moon, Sun, LogOut, HelpCircle } from 'lucide-react'
import Tour from './Tour'

export default function Layout({ children, darkMode, setDarkMode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [tourRunning, setTourRunning] = useState(() => !localStorage.getItem('dq_tour_done'))
  const location = useLocation()

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode
    setDarkMode(newDarkMode)
    if (newDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const navItems = [
    { path: '/', label: 'Home', icon: '🏠', tour: 'nav-home' },
    { path: '/alerts', label: 'Alerts', icon: '🔔', tour: 'nav-alerts' },
    { path: '/reports', label: 'Reports', icon: '📄', tour: 'nav-reports' },
    { path: '/configuration', label: 'Settings', icon: '⚙️', tour: 'nav-settings' },
  ]

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300 flex flex-col shadow-lg`}>
        {/* Logo */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center text-white font-bold text-lg">
                🔍
              </div>
              <div>
                <h1 className="font-bold text-lg dark:text-white">DataQ</h1>
                <p className="text-xs text-gray-500">Quality Monitor</p>
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              data-tour={item.tour}
              className={`sidebar-link flex items-center gap-3 ${
                location.pathname === item.path ? 'active' : ''
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-800 space-y-2">
          <button
            onClick={() => setTourRunning(true)}
            className="sidebar-link w-full flex items-center gap-3 justify-center"
          >
            <HelpCircle size={18} />
            {sidebarOpen && <span>Take a Tour</span>}
          </button>
          <button
            data-tour="theme-toggle"
            onClick={toggleDarkMode}
            className="sidebar-link w-full flex items-center gap-3 justify-center"
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            {sidebarOpen && <span>{darkMode ? 'Light' : 'Dark'}</span>}
          </button>
          <button className="sidebar-link w-full flex items-center gap-3 justify-center text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">
            <LogOut size={18} />
            {sidebarOpen && <span>Exit</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-8 py-4 shadow-sm flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Data Quality Checker</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">Upload data, run a check, see the results</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-green-700 dark:text-green-400">System Online</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          <div className="p-8">
            {children}
          </div>
        </main>
      </div>

      {tourRunning && (
        <Tour
          onFinish={() => {
            setTourRunning(false)
            localStorage.setItem('dq_tour_done', '1')
          }}
        />
      )}
    </div>
  )
}
