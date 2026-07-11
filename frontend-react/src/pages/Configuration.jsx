import React, { useState } from 'react'
import Card from '../components/Card'
import Button from '../components/Button'
import Alert from '../components/Alert'
import { Save } from 'lucide-react'

export default function Configuration() {
  const [config, setConfig] = useState({
    smtp_enabled: false,
    smtp_host: 'smtp.gmail.com',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    alert_email: '',
    null_threshold: 0.1,
    outlier_threshold: 0.05,
    drift_threshold: 0.05,
    freshness_hours: 24,
  })
  const [saved, setSaved] = useState(false)

  const handleChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }))
    setSaved(false)
  }

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">⚙️ Settings</h1>
        <p className="text-gray-600 dark:text-gray-400">Adjust how sensitive checks are and how alerts are sent</p>
      </div>

      <Alert
        type="info"
        title="Preview only"
        message="These settings aren't connected to the server yet — changing them here won't affect your checks. To make them take effect, they need to be wired up to the backend."
      />

      {saved && <Alert type="success" message="Saved locally (not yet sent to the server)" />}

      {/* Quality Thresholds */}
      <Card>
        <h3 className="text-lg font-semibold mb-6">📊 Quality Thresholds</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium mb-2">Null Value Threshold</label>
            <div className="flex gap-2 items-center">
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={config.null_threshold}
                onChange={(e) => handleChange('null_threshold', parseFloat(e.target.value))}
                className="flex-1 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg"
              />
              <span className="text-gray-600 dark:text-gray-400">{(config.null_threshold * 100).toFixed(0)}%</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">Alert when null values exceed this threshold</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Outlier Threshold</label>
            <div className="flex gap-2 items-center">
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={config.outlier_threshold}
                onChange={(e) => handleChange('outlier_threshold', parseFloat(e.target.value))}
                className="flex-1 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg"
              />
              <span className="text-gray-600 dark:text-gray-400">{(config.outlier_threshold * 100).toFixed(0)}%</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">IQR multiplier for outlier detection</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Drift Threshold</label>
            <div className="flex gap-2 items-center">
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={config.drift_threshold}
                onChange={(e) => handleChange('drift_threshold', parseFloat(e.target.value))}
                className="flex-1 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg"
              />
              <span className="text-gray-600 dark:text-gray-400">{(config.drift_threshold * 100).toFixed(0)}%</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">P-value threshold for statistical tests</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Freshness Check (hours)</label>
            <input
              type="number"
              min="1"
              value={config.freshness_hours}
              onChange={(e) => handleChange('freshness_hours', parseInt(e.target.value))}
              className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg"
            />
            <p className="text-xs text-gray-500 mt-1">Alert if data not updated within this period</p>
          </div>
        </div>
      </Card>

      {/* Email Configuration */}
      <Card>
        <h3 className="text-lg font-semibold mb-6">📧 Email Alerts</h3>

        <div className="space-y-4">
          <div>
            <label className="flex items-center gap-2 mb-4">
              <input
                type="checkbox"
                checked={config.smtp_enabled}
                onChange={(e) => handleChange('smtp_enabled', e.target.checked)}
                className="w-4 h-4"
              />
              <span className="font-medium">Enable Email Alerts</span>
            </label>
          </div>

          {config.smtp_enabled && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div>
                <label className="block text-sm font-medium mb-2">SMTP Host</label>
                <input
                  type="text"
                  value={config.smtp_host}
                  onChange={(e) => handleChange('smtp_host', e.target.value)}
                  className="w-full px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">SMTP Port</label>
                <input
                  type="number"
                  value={config.smtp_port}
                  onChange={(e) => handleChange('smtp_port', parseInt(e.target.value))}
                  className="w-full px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">SMTP Username</label>
                <input
                  type="text"
                  value={config.smtp_user}
                  onChange={(e) => handleChange('smtp_user', e.target.value)}
                  className="w-full px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">SMTP Password</label>
                <input
                  type="password"
                  value={config.smtp_password}
                  onChange={(e) => handleChange('smtp_password', e.target.value)}
                  className="w-full px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-2">Alert Email Address</label>
                <input
                  type="email"
                  value={config.alert_email}
                  onChange={(e) => handleChange('alert_email', e.target.value)}
                  className="w-full px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
                  placeholder="alerts@example.com"
                />
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave}>
          <Save size={16} className="inline mr-2" />
          Save Configuration
        </Button>
      </div>

      {/* Info */}
      <Card>
        <h3 className="text-lg font-semibold mb-3">ℹ️ Configuration Help</h3>
        <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li><strong>Quality Thresholds:</strong> Define sensitivity levels for alerts</li>
          <li><strong>Email Alerts:</strong> Send notifications when issues are detected</li>
          <li><strong>Freshness Check:</strong> Monitor if data is being updated regularly</li>
          <li><strong>SMTP Configuration:</strong> Use Gmail (enable "App Password"), SendGrid, or your SMTP provider</li>
        </ul>
      </Card>
    </div>
  )
}
