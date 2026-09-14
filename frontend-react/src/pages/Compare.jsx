import React, { useState } from 'react'
import Card from '../components/Card'
import Button from '../components/Button'
import Alert from '../components/Alert'
import { apiService } from '../utils/api'
import { Upload, GitCompare } from 'lucide-react'

export default function Compare() {
  const [fileA, setFileA] = useState(null)
  const [fileB, setFileB] = useState(null)
  const [comparing, setComparing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleCompare = async () => {
    if (!fileA || !fileB) return
    try {
      setComparing(true)
      setError(null)
      const res = await apiService.compareFiles(fileA, fileB)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not compare these files. Make sure both are valid CSV/Excel/Parquet files.')
      setResult(null)
    } finally {
      setComparing(false)
    }
  }

  const qualityScore = result?.overall_similarity_score ?? null
  const scoreColor = qualityScore === null ? 'gray'
    : qualityScore >= 0.8 ? 'green'
    : qualityScore >= 0.6 ? 'yellow'
    : 'red'

  const nullAnalysis = result?.anomaly_detection?.null_analysis || {}
  const outlierAnalysis = result?.anomaly_detection?.outliers || {}

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold mb-1">Compare Two Files ⚖️</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Pick any two files and see how they differ — no baseline, no saved history, just a direct one-off comparison.
          Want to track one file's quality over time instead? Go to <span className="font-semibold text-primary">Home</span> in the sidebar.
        </p>
      </div>

      {error && <Alert type="critical" title="Something went wrong" message={error} onDismiss={() => setError(null)} />}

      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FileSlot
            label="File A (the reference)"
            file={fileA}
            onSelect={setFileA}
            inputId="file-a-input"
          />
          <FileSlot
            label="File B (checked against A)"
            file={fileB}
            onSelect={setFileB}
            inputId="file-b-input"
          />
        </div>
        <div className="mt-5 flex justify-end">
          <Button onClick={handleCompare} disabled={!fileA || !fileB || comparing}>
            <GitCompare size={16} className="inline mr-2" />
            {comparing ? 'Comparing…' : 'Compare Files'}
          </Button>
        </div>
      </Card>

      {result && (
        <Card>
          <div className="text-xs px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 mb-6">
            File A: <span className="font-semibold">{result.file_a.filename}</span> ({result.file_a.row_count.toLocaleString()} rows) &nbsp;vs&nbsp;
            File B: <span className="font-semibold">{result.file_b.filename}</span> ({result.file_b.row_count.toLocaleString()} rows)
          </div>

          <div className="flex items-center gap-6 p-5 rounded-lg mb-6" style={{
            background: scoreColor === 'green' ? 'rgba(82,196,26,0.08)'
              : scoreColor === 'yellow' ? 'rgba(255,169,77,0.1)'
              : scoreColor === 'red' ? 'rgba(255,107,107,0.08)'
              : 'rgba(156,163,175,0.08)'
          }}>
            <div className="text-center flex-shrink-0">
              <p className="text-4xl font-bold" style={{color: scoreColor === 'green' ? '#52c41a' : scoreColor === 'yellow' ? '#ffa94d' : scoreColor === 'red' ? '#ff6b6b' : '#9ca3af'}}>
                {(qualityScore * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">Similarity Score</p>
            </div>
            <div>
              <p className="font-semibold text-lg">
                {qualityScore >= 0.8 ? '✅ These files look very similar' : qualityScore >= 0.6 ? '🟡 Some notable differences' : '🔴 Significant differences found'}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Row count: A has {result.file_a.row_count.toLocaleString()}, B has {result.file_b.row_count.toLocaleString()}
                {' '}({result.row_count_diff >= 0 ? '+' : ''}{result.row_count_diff}, {result.row_count_diff_percent.toFixed(1)}%)
              </p>
            </div>
          </div>

          {/* Schema diff */}
          <div className="mb-6">
            <p className="font-semibold mb-2">Structure (Schema) Differences</p>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              {result.schema_validation?.change_count || 0} change(s)
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
              <p className="text-sm text-gray-500">Both files have the same columns and types.</p>
            )}
          </div>

          {/* Drift */}
          <div className="mb-6">
            <p className="font-semibold mb-2">Distribution Drift (A → B)</p>
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

          {/* Anomalies in File B */}
          <div>
            <p className="font-semibold mb-2">Missing Values in File B</p>
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
              <p className="text-sm text-gray-500">No missing values found in File B.</p>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}

function FileSlot({ label, file, onSelect, inputId }) {
  return (
    <div>
      <p className="text-sm font-medium mb-2">{label}</p>
      <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 text-center hover:border-primary transition">
        <input
          type="file"
          onChange={(e) => onSelect(e.target.files[0] || null)}
          accept=".csv,.parquet,.xlsx,.xls"
          className="hidden"
          id={inputId}
        />
        <label htmlFor={inputId} className="cursor-pointer block">
          <Upload size={28} className="mx-auto mb-2 text-gray-400" />
          <p className="font-medium text-sm truncate">
            {file ? file.name : 'Click to choose a file'}
          </p>
        </label>
      </div>
    </div>
  )
}
