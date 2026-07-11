import React, { useState, useEffect } from 'react'
import Card from '../components/Card'
import Button from '../components/Button'
import Loading from '../components/Loading'
import ErrorDisplay from '../components/ErrorDisplay'
import Alert from '../components/Alert'
import { apiService } from '../utils/api'
import { CheckCircle } from 'lucide-react'

const FRIENDLY_NAMES = {
  schema_missing_column: 'A column went missing',
  schema_new_column: 'A new column appeared',
  schema_type_change: 'A column changed type',
  distribution_drift: 'Data pattern changed',
  feature_drift: 'A column\'s pattern changed',
  high_null_rate: 'Too many blank values',
}

function friendlyLabel(metricType) {
  return FRIENDLY_NAMES[metricType] || metricType?.replace(/_/g, ' ')
}

export default function AlertsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [summary, setSummary] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      setError(null)
      const datasetsRes = await apiService.getDatasets()
      const datasets = datasetsRes.data.datasets || []
      if (datasets.length === 0) {
        setAlerts([])
        setSummary(null)
        setLoading(false)
        return
      }

      const alertsRes = await apiService.getAlerts(datasets[0].id)
      setAlerts(alertsRes.data.alerts || [])

      const summaryRes = await apiService.getAlertSummary(datasets[0].id)
      setSummary(summaryRes.data)
    } catch (err) {
      console.error('Error loading alerts:', err)
      setAlerts([])
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }

  const handleAcknowledge = async (alertId) => {
    try {
      await apiService.acknowledgeAlert(alertId)
      await loadAlerts()
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) return <Loading />

  if (alerts.length === 0 && !summary) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">🔔 Alerts</h1>
        <Card className="text-center py-12">
          <p className="text-gray-500">No files uploaded yet</p>
          <p className="text-sm text-gray-400 mt-2">Go to Home and upload a file to start seeing alerts here</p>
        </Card>
      </div>
    )
  }

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter(a => a.severity.toLowerCase() === filter)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">🔔 Alerts</h1>
        <p className="text-gray-600 dark:text-gray-400">Monitor data quality issues and notifications</p>
      </div>

      {error && <ErrorDisplay message={error} retry={loadAlerts} />}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="metric-card bg-gradient-primary">
            <p className="text-sm opacity-90">Critical Alerts</p>
            <p className="text-3xl font-bold mt-2">{summary.critical_count || 0}</p>
          </div>
          <div className="metric-card bg-gradient-warning">
            <p className="text-sm opacity-90">Warnings</p>
            <p className="text-3xl font-bold mt-2">{summary.warning_count || 0}</p>
          </div>
          <div className="metric-card bg-gradient-success">
            <p className="text-sm opacity-90">Info</p>
            <p className="text-3xl font-bold mt-2">{summary.info_count || 0}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'critical', 'warning', 'info'].map(f => (
          <Button
            key={f}
            variant={filter === f ? 'primary' : 'secondary'}
            onClick={() => setFilter(f)}
            className="capitalize"
          >
            {f}
          </Button>
        ))}
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <Card className="text-center py-12">
            <CheckCircle size={48} className="mx-auto text-green-600 mb-3" />
            <p className="text-green-600 font-semibold">No alerts</p>
            <p className="text-gray-500 text-sm mt-2">Your data quality is excellent!</p>
          </Card>
        ) : (
          filteredAlerts.map((alert) => {
            const severityColor = {
              critical: 'alert-critical',
              warning: 'alert-warning',
              info: 'alert-info'
            }
            return (
              <Card key={alert.id} className={`${severityColor[alert.severity.toLowerCase()]}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold">{friendlyLabel(alert.metric_type)}</p>
                    <p className="text-sm mt-1">{alert.message}</p>
                    <p className="text-xs opacity-75 mt-2">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  {alert.status !== 'ACKNOWLEDGED' ? (
                    <Button
                      variant="secondary"
                      onClick={() => handleAcknowledge(alert.id)}
                      className="!px-3 !py-1 text-sm"
                    >
                      Mark as Reviewed
                    </Button>
                  ) : (
                    <span className="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm font-medium">
                      ✓ Reviewed
                    </span>
                  )}
                </div>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
