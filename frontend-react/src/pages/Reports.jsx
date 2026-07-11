import React, { useState, useEffect } from 'react'
import Card from '../components/Card'
import Button from '../components/Button'
import Loading from '../components/Loading'
import Alert from '../components/Alert'
import { apiService } from '../utils/api'
import { Download } from 'lucide-react'

export default function Reports() {
  const [loading, setLoading] = useState(true)
  const [dataset, setDataset] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [format, setFormat] = useState('text')
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDataset()
  }, [])

  const loadDataset = async () => {
    try {
      setLoading(true)
      const datasetsRes = await apiService.getDatasets()
      const datasets = datasetsRes.data.datasets || []
      setDataset(datasets[0] || null)
    } catch (err) {
      setError('Could not load your files.')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!dataset) return
    try {
      setGenerating(true)
      setError(null)
      const res = await apiService.getReport(dataset.id, format)
      const content = format === 'text'
        ? res.data.content
        : JSON.stringify(res.data, null, 2)
      const link = document.createElement('a')
      link.href = URL.createObjectURL(new Blob([content], { type: format === 'text' ? 'text/plain' : 'application/json' }))
      link.download = `data-quality-report-${new Date().toISOString().split('T')[0]}.${format === 'json' ? 'json' : 'txt'}`
      link.click()
    } catch (err) {
      setError(
        err.response?.status === 404
          ? 'No results yet for this file — go to Home and click "Run Check" first.'
          : 'Could not generate the report.'
      )
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <Loading />

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold mb-2">📄 Reports</h1>
        <p className="text-gray-600 dark:text-gray-400">Download a summary of your data quality results</p>
      </div>

      {error && <Alert type="critical" message={error} onDismiss={() => setError(null)} />}

      {!dataset ? (
        <Card className="text-center py-12">
          <p className="text-gray-500">No files uploaded yet</p>
          <p className="text-sm text-gray-400 mt-2">Go to Home and upload a file first</p>
        </Card>
      ) : (
        <Card>
          <h3 className="text-lg font-semibold mb-1">{dataset.name}</h3>
          <p className="text-sm text-gray-500 mb-4">Download a report for this file</p>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">Format</label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg"
              >
                <option value="text">Plain text (easy to read)</option>
                <option value="json">JSON (for developers)</option>
              </select>
            </div>
            <Button onClick={handleDownload} disabled={generating}>
              <Download size={16} className="inline mr-2" />
              {generating ? 'Preparing…' : 'Download Report'}
            </Button>
          </div>
        </Card>
      )}

      <Card>
        <h3 className="text-lg font-semibold mb-3">What's in the report?</h3>
        <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li>• A summary of your data's overall quality score</li>
          <li>• Missing values, unusual values, and rule violations found</li>
          <li>• Any structure changes since the last check</li>
          <li>• A list of alerts raised during the check</li>
        </ul>
      </Card>
    </div>
  )
}
