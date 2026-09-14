import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const apiService = {
  // Datasets
  getDatasets: () => api.get('/datasets'),
  uploadDataset: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  deleteDataset: (datasetId) => api.delete(`/datasets/${datasetId}`),

  // Versions — multiple files can each be checked against the same fixed baseline
  uploadDatasetVersion: (datasetId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/datasets/${datasetId}/versions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getDatasetVersions: (datasetId) => api.get(`/datasets/${datasetId}/versions`),
  deleteDatasetVersion: (datasetId, versionId) => api.delete(`/datasets/${datasetId}/versions/${versionId}`),
  promoteVersionToBaseline: (datasetId, versionId) =>
    api.post(`/datasets/${datasetId}/versions/${versionId}/promote`),
  getBaselineHistory: (datasetId) => api.get(`/datasets/${datasetId}/baseline-history`),

  // Analysis — pass versionId to check a specific uploaded version against the baseline
  runAnalysis: (datasetId, versionId) =>
    api.post(`/datasets/${datasetId}/analyze`, null, { params: versionId ? { version_id: versionId } : {} }),

  // Results
  getLatestResult: (datasetId, versionId) =>
    api.get(`/datasets/${datasetId}/latest-result`, { params: versionId ? { version_id: versionId } : {} }),
  getMetricHistory: (datasetId) => api.get(`/datasets/${datasetId}/metric-history`),

  // Alerts
  getAlerts: (datasetId) => api.get('/alerts', { params: { dataset_id: datasetId } }),
  getAlertSummary: (datasetId) => api.get(`/alerts/dataset/${datasetId}/summary`),
  acknowledgeAlert: (alertId) => api.post(`/alerts/${alertId}/acknowledge`),

  // Reports
  getReport: (datasetId, format = 'text') =>
    api.get(`/datasets/${datasetId}/report`, { params: { format } }),

  // Compare two independent files directly (no persisted baseline)
  compareFiles: (fileA, fileB) => {
    const formData = new FormData()
    formData.append('file_a', fileA)
    formData.append('file_b', fileB)
    return api.post('/compare', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Health
  getHealth: () => api.get('/health'),
}

export default api
