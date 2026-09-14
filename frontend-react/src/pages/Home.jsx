import React, { useState, useEffect } from 'react'
import Card from '../components/Card'
import Button from '../components/Button'
import Alert from '../components/Alert'
import { apiService } from '../utils/api'
import { Upload, RefreshCw, CheckCircle2, Trash2, ChevronDown, ChevronUp, RotateCw } from 'lucide-react'

export default function Home() {
  const [datasets, setDatasets] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [result, setResult] = useState(null)
  const [alertSummary, setAlertSummary] = useState(null)
  const [loadingList, setLoadingList] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [loadingResult, setLoadingResult] = useState(false)
  const [error, setError] = useState(null)
  const [banner, setBanner] = useState(null) // { type, message }
  const [showDetails, setShowDetails] = useState(false)
  const [uploadingVersion, setUploadingVersion] = useState(false)

  useEffect(() => {
    loadDatasets()
  }, [])

  useEffect(() => {
    if (activeId) loadResult(activeId)
    else setResult(null)
  }, [activeId])

  const loadDatasets = async (preferId) => {
    try {
      setLoadingList(true)
      const res = await apiService.getDatasets()
      const list = res.data.datasets || []
      setDatasets(list)
      if (list.length > 0) {
        const stillExists = preferId && list.some(d => d.id === preferId)
        setActiveId(stillExists ? preferId : list[0].id)
      } else {
        setActiveId(null)
      }
    } catch (err) {
      setError('Could not load your datasets. Is the server running?')
    } finally {
      setLoadingList(false)
    }
  }

  const loadResult = async (datasetId) => {
    try {
      setLoadingResult(true)
      setError(null)
      const [resultRes, summaryRes] = await Promise.allSettled([
        apiService.getLatestResult(datasetId),
        apiService.getAlertSummary(datasetId),
      ])
      setResult(resultRes.status === 'fulfilled' ? resultRes.value.data : null)
      setAlertSummary(summaryRes.status === 'fulfilled' ? summaryRes.value.data : null)
    } finally {
      setLoadingResult(false)
    }
  }

  const handleFileSelect = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      setUploading(true)
      setError(null)
      const res = await apiService.uploadDataset(file)
      const newId = res.data?.dataset_id
      setBanner({ type: 'success', message: `"${file.name}" uploaded successfully.` })
      await loadDatasets(newId)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please check the file and try again.')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleRunCheck = async () => {
    if (!activeId) return
    try {
      setAnalyzing(true)
      setError(null)
      await apiService.runAnalysis(activeId)
      setBanner({ type: 'success', message: 'Check complete! Here are your results.' })
      await loadResult(activeId)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not run the check on this dataset.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleDelete = async (datasetId) => {
    if (!window.confirm('Remove this dataset? This cannot be undone.')) return
    try {
      await apiService.deleteDataset(datasetId)
      await loadDatasets()
    } catch (err) {
      setError('Could not delete this dataset.')
    }
  }

  const handleUploadNewVersion = async (e) => {
    const file = e.target.files[0]
    if (!file || !activeId) return
    try {
      setUploadingVersion(true)
      setError(null)
      await apiService.uploadNewVersion(activeId, file)
      setBanner({ type: 'success', message: 'New data uploaded. Click "Run Check" to compare it against the original baseline.' })
      await loadDatasets(activeId)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not upload the new data.')
    } finally {
      setUploadingVersion(false)
      e.target.value = ''
    }
  }

  const activeDataset = datasets.find(d => d.id === activeId)
  // Compute this from the two filenames directly rather than trusting a
  // backend-provided flag — the list endpoint doesn't always include it.
  const hasNewVersion = (ds) => !!ds && !!ds.current_filename && ds.current_filename !== ds.baseline_filename
  const qualityScore = result?.overall_quality_score ?? null
  const scoreLabel = qualityScore === null ? null
    : qualityScore >= 0.8 ? 'Good'
    : qualityScore >= 0.6 ? 'Okay'
    : 'Needs Attention'
  const scoreColor = qualityScore === null ? 'gray'
    : qualityScore >= 0.8 ? 'green'
    : qualityScore >= 0.6 ? 'yellow'
    : 'red'

  // Derive plain-language numbers from the real nested result shape
  const nullAnalysis = result?.anomaly_detection?.null_analysis || {}
  const outlierAnalysis = result?.anomaly_detection?.outliers || {}
  const domainViolations = result?.anomaly_detection?.domain_violations || {}
  const missingCount = Object.values(nullAnalysis).reduce((sum, c) => sum + (c.null_count || 0), 0)
  const outlierCount = Object.values(outlierAnalysis).reduce((sum, c) => sum + (c.outlier_count || 0), 0)
  const ruleViolationCount = Object.values(domainViolations).reduce((sum, c) => sum + (c.count || 0), 0)
  const schemaChangeCount = result?.schema_validation?.change_count || 0

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold mb-1">Track One Dataset Over Time 🔁</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Upload a file to lock in a baseline, then check it again over time to catch drift and changes.
          Want to compare two files directly instead? Go to <span className="font-semibold text-primary">Compare</span> in the sidebar.
        </p>
      </div>

      {banner && (
        <Alert type={banner.type} message={banner.message} onDismiss={() => setBanner(null)} />
      )}
      {error && <Alert type="critical" title="Something went wrong" message={error} onDismiss={() => setError(null)} />}

      {/* STEP 1: Upload */}
      <Card data-tour="upload-card">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-7 h-7 rounded-full bg-gradient-primary text-white flex items-center justify-center text-sm font-bold">1</span>
          <h3 className="text-lg font-semibold">Upload your data file</h3>
        </div>
        <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-8 text-center hover:border-primary transition">
          <input
            type="file"
            onChange={handleFileSelect}
            accept=".csv,.parquet,.xlsx,.xls"
            className="hidden"
            id="file-input"
            disabled={uploading}
          />
          <label htmlFor="file-input" className="cursor-pointer block">
            <Upload size={40} className="mx-auto mb-3 text-gray-400" />
            <p className="font-semibold mb-1">
              {uploading ? 'Uploading…' : 'Click here to choose a file'}
            </p>
            <p className="text-sm text-gray-500">Works with CSV, Excel, or Parquet files</p>
          </label>
        </div>
      </Card>

      {/* STEP 2: Pick which dataset + Run check */}
      <Card data-tour="choose-run-card">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-7 h-7 rounded-full bg-gradient-primary text-white flex items-center justify-center text-sm font-bold">2</span>
          <h3 className="text-lg font-semibold">Choose a file and run a check</h3>
        </div>

        {loadingList ? (
          <p className="text-gray-500 text-sm">Loading your files…</p>
        ) : datasets.length === 0 ? (
          <p className="text-gray-500 text-sm">No files uploaded yet — upload one above to get started.</p>
        ) : (
          <div className="space-y-2">
            {datasets.map((ds) => (
              <div
                key={ds.id}
                onClick={() => setActiveId(ds.id)}
                className={`flex items-center justify-between p-4 rounded-lg cursor-pointer border transition ${
                  ds.id === activeId
                    ? 'border-primary bg-primary/5 dark:bg-primary/10'
                    : 'border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                <div className="flex items-center gap-3">
                  {ds.id === activeId ? (
                    <CheckCircle2 size={20} className="text-primary flex-shrink-0" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-gray-300 dark:border-gray-600 flex-shrink-0" />
                  )}
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">{ds.name}</p>
                    <p className="text-xs text-gray-500">
                      {ds.row_count?.toLocaleString()} rows · {ds.column_count} columns · baseline established {new Date(ds.created_at).toLocaleDateString()}
                    </p>
                    {hasNewVersion(ds) ? (
                      <p className="text-xs text-primary font-medium mt-0.5">
                        → Currently checking new data: {ds.current_filename} (uploaded {new Date(ds.current_file_uploaded_at).toLocaleString()})
                      </p>
                    ) : (
                      <p className="text-xs text-gray-400 mt-0.5">
                        No new data uploaded yet — a check right now compares this file against itself
                      </p>
                    )}
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(ds.id) }}
                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                  title="Remove this file"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}

        {activeDataset && (
          <div className="mt-5 flex items-center justify-between flex-wrap gap-3">
            <div>
              <input
                type="file"
                onChange={handleUploadNewVersion}
                accept=".csv,.parquet,.xlsx,.xls"
                className="hidden"
                id="new-version-input"
                disabled={uploadingVersion}
              />
              <label
                htmlFor="new-version-input"
                className="inline-flex items-center gap-2 text-sm text-primary hover:underline cursor-pointer"
              >
                <RotateCw size={14} />
                {uploadingVersion ? 'Uploading…' : 'Upload newer data to replace the current file (baseline stays locked)'}
              </label>
            </div>
            <Button onClick={handleRunCheck} disabled={analyzing}>
              <RefreshCw size={16} className="inline mr-2" />
              {analyzing ? 'Checking…' : `Run Check on "${activeDataset.name}"`}
            </Button>
          </div>
        )}
      </Card>

      {/* STEP 3: Results */}
      <Card data-tour="results-card">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-7 h-7 rounded-full bg-gradient-primary text-white flex items-center justify-center text-sm font-bold">3</span>
          <h3 className="text-lg font-semibold">Results</h3>
        </div>

        {!activeDataset ? (
          <p className="text-gray-500 text-sm py-6 text-center">
            Upload a file above to see results here.
          </p>
        ) : loadingResult ? (
          <p className="text-gray-500 text-sm">Loading results…</p>
        ) : !result ? (
          <p className="text-gray-500 text-sm py-6 text-center">
            No results yet — click "Run Check" above to analyze this file.
          </p>
        ) : (
            <div className="space-y-6">
              {/* Which files this result actually compares */}
              <div className="text-xs px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                Comparing <span className="font-semibold">{activeDataset.current_filename}</span> against the baseline
                (<span className="font-semibold">{activeDataset.baseline_filename}</span>, established {new Date(activeDataset.created_at).toLocaleDateString()})
                {!hasNewVersion(activeDataset) && ' — same file, so schema/drift show no change until you upload newer data'}
              </div>

              {/* Overall score */}
              <div
                className="flex items-center gap-6 p-5 rounded-lg"
                style={{
                  background: scoreColor === 'green' ? 'rgba(82,196,26,0.08)'
                    : scoreColor === 'yellow' ? 'rgba(255,169,77,0.1)'
                    : scoreColor === 'red' ? 'rgba(255,107,107,0.08)'
                    : 'rgba(156,163,175,0.08)'
                }}
              >
                <div className="text-center flex-shrink-0">
                  <p className="text-4xl font-bold" style={{color: scoreColor === 'green' ? '#52c41a' : scoreColor === 'yellow' ? '#ffa94d' : scoreColor === 'red' ? '#ff6b6b' : '#9ca3af'}}>
                    {(qualityScore * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Overall Score</p>
                </div>
                <div>
                  <p className="font-semibold text-lg">
                    {scoreLabel === 'Good' && '✅ Your data looks good'}
                    {scoreLabel === 'Okay' && '🟡 Your data is okay, but could be better'}
                    {scoreLabel === 'Needs Attention' && '🔴 Your data needs attention'}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Based on missing values, duplicates, unusual entries, and changes since the last check.
                  </p>
                </div>
              </div>

              {/* Plain-language breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <PlainMetric
                  label="Missing information"
                  value={missingCount}
                  good={missingCount === 0}
                  hint="Cells that are empty or blank"
                />
                <PlainMetric
                  label="Unusual values"
                  value={outlierCount}
                  good={outlierCount === 0}
                  hint="Numbers that look far outside the normal range"
                />
                <PlainMetric
                  label="Rule violations"
                  value={ruleViolationCount}
                  good={ruleViolationCount === 0}
                  hint="Values that break an expected rule (e.g. negative age)"
                />
                <PlainMetric
                  label="Structure changes"
                  value={schemaChangeCount}
                  good={schemaChangeCount === 0}
                  hint="Columns added, removed, or changed type"
                />
              </div>

              {result.completeness?.overall_status && result.completeness.overall_status !== 'OK' && (
                <Alert
                  type={result.completeness.overall_status === 'CRITICAL' ? 'critical' : 'warning'}
                  title="Data freshness or coverage issue"
                  message={`Completeness check status: ${result.completeness.overall_status}. This usually means the data is outdated or missing expected records.`}
                />
              )}

              {/* Alerts inline */}
              <div>
                <p className="font-semibold mb-2">Alerts</p>
                {(!alertSummary || ((alertSummary.critical_count || 0) === 0 && (alertSummary.warning_count || 0) === 0)) ? (
                  <Alert type="success" message="No alerts — nothing urgent to review." />
                ) : (
                  <div className="space-y-2">
                    {alertSummary.critical_count > 0 && (
                      <Alert type="critical" title="Critical" message={`${alertSummary.critical_count} critical issue(s) found. Check the Alerts page for details.`} />
                    )}
                    {alertSummary.warning_count > 0 && (
                      <Alert type="warning" title="Warning" message={`${alertSummary.warning_count} warning(s) found. Check the Alerts page for details.`} />
                    )}
                  </div>
                )}
              </div>

              {/* Detailed technical breakdown (schema, drift, anomalies) */}
              <div className="border-t border-gray-200 dark:border-gray-800 pt-4">
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="flex items-center gap-2 text-sm font-semibold text-primary hover:underline"
                >
                  {showDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  {showDetails ? 'Hide detailed technical breakdown' : 'Show detailed technical breakdown'}
                </button>

                {showDetails && (
                  <div className="mt-4 space-y-6">
                    {/* Schema validation */}
                    <div>
                      <p className="font-semibold mb-2">Schema Validation</p>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        {result.schema_validation?.change_count || 0} change(s) detected
                        {result.schema_validation?.is_breaking ? ' — includes breaking changes ⚠️' : ' — no breaking changes ✅'}
                      </div>
                      {result.schema_validation?.changes?.length > 0 ? (
                        <div className="space-y-1">
                          {result.schema_validation.changes.map((c, i) => (
                            <div key={i} className="text-sm p-2 bg-gray-50 dark:bg-gray-800 rounded flex items-center justify-between">
                              <span>
                                <span className="font-medium">{c.type?.replace(/_/g, ' ')}</span>: {c.column}
                                {c.old && c.new && <span className="text-gray-500"> ({c.old} → {c.new})</span>}
                              </span>
                              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                c.severity === 'CRITICAL' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                : c.severity === 'WARNING' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                                : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                              }`}>{c.severity}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No columns were added, removed, or changed type.</p>
                      )}
                    </div>

                    {/* Distribution drift */}
                    <div>
                      <p className="font-semibold mb-2">Distribution Drift</p>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        Overall drift score: <span className="font-medium">{(result.drift_analysis?.overall_drift_score ?? 0).toFixed(3)}</span>
                        {' · '}Severity: <span className="font-medium">{result.drift_analysis?.severity_level || 'INFO'}</span>
                        {' · '}{result.drift_analysis?.drifted_count || 0} of {result.drift_analysis?.feature_count || 0} column(s) drifted
                      </div>
                      {result.drift_analysis?.drifted_features?.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
                                <th className="py-1 pr-4">Column</th>
                                <th className="py-1 pr-4">Drift Score</th>
                                <th className="py-1 pr-4">P-Value</th>
                                <th className="py-1">Test</th>
                              </tr>
                            </thead>
                            <tbody>
                              {result.drift_analysis.drifted_features.map((f, i) => (
                                <tr key={i} className="border-b border-gray-100 dark:border-gray-800">
                                  <td className="py-1 pr-4 font-medium">{f.feature}</td>
                                  <td className="py-1 pr-4">{f.drift_score?.toFixed(3)}</td>
                                  <td className="py-1 pr-4">{f.p_value?.toFixed(4)}</td>
                                  <td className="py-1">{f.test_method}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No columns showed a significant shift in distribution.</p>
                      )}
                    </div>

                    {/* Per-column anomalies */}
                    <div>
                      <p className="font-semibold mb-2">Missing Values by Column</p>
                      {Object.keys(nullAnalysis).length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
                                <th className="py-1 pr-4">Column</th>
                                <th className="py-1 pr-4">Missing Count</th>
                                <th className="py-1 pr-4">Missing Rate</th>
                                <th className="py-1">Status</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries(nullAnalysis).map(([col, info]) => (
                                <tr key={col} className="border-b border-gray-100 dark:border-gray-800">
                                  <td className="py-1 pr-4 font-medium">{col}</td>
                                  <td className="py-1 pr-4">{info.null_count}</td>
                                  <td className="py-1 pr-4">{((info.null_rate || 0) * 100).toFixed(1)}%</td>
                                  <td className="py-1">{info.status}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No missing values found in any column.</p>
                      )}
                    </div>

                    <div>
                      <p className="font-semibold mb-2">Unusual Values (Outliers) by Column</p>
                      {Object.keys(outlierAnalysis).length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
                                <th className="py-1 pr-4">Column</th>
                                <th className="py-1 pr-4">Outlier Count</th>
                                <th className="py-1 pr-4">Percentage</th>
                                <th className="py-1">Method</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries(outlierAnalysis).map(([col, info]) => (
                                <tr key={col} className="border-b border-gray-100 dark:border-gray-800">
                                  <td className="py-1 pr-4 font-medium">{col}</td>
                                  <td className="py-1 pr-4">{info.outlier_count}</td>
                                  <td className="py-1 pr-4">{(info.percentage || 0).toFixed(1)}%</td>
                                  <td className="py-1">{info.method}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No unusual values found in any column.</p>
                      )}
                    </div>

                    {/* Completeness detail */}
                    <div>
                      <p className="font-semibold mb-2">Completeness</p>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                          <p className="text-gray-500 text-xs">Completeness Score</p>
                          <p className="font-semibold">{((result.completeness?.completeness_score || 0) * 100).toFixed(1)}%</p>
                        </div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                          <p className="text-gray-500 text-xs">Row Count</p>
                          <p className="font-semibold">{result.completeness?.record_count?.current_count?.toLocaleString() ?? 'N/A'}</p>
                        </div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                          <p className="text-gray-500 text-xs">Hours Since Last Update</p>
                          <p className="font-semibold">{result.completeness?.freshness?.hours_since_update?.toFixed(1) ?? 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
        )}
      </Card>
    </div>
  )
}

function PlainMetric({ label, value, good, hint }) {
  return (
    <div className={`p-4 rounded-lg border ${good ? 'border-green-200 dark:border-green-900 bg-green-50/50 dark:bg-green-900/10' : 'border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800'}`}>
      <div className="flex items-center justify-between">
        <p className="font-medium text-sm">{label}</p>
        <p className={`text-xl font-bold ${good ? 'text-green-600' : 'text-gray-900 dark:text-white'}`}>{value}</p>
      </div>
      <p className="text-xs text-gray-500 mt-1">{hint}</p>
    </div>
  )
}
