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
  uploadNewVersion: (datasetId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/datasets/${datasetId}/upload-version`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Analysis
  runAnalysis: (datasetId) => api.post(`/datasets/${datasetId}/analyze`),

  // Results
  getLatestResult: (datasetId) => api.get(`/datasets/${datasetId}/latest-result`),
  getMetricHistory: (datasetId) => api.get(`/datasets/${datasetId}/metric-history`),

  // Alerts
  getAlerts: (datasetId) => api.get('/alerts', { params: { dataset_id: datasetId } }),
  getAlertSummary: (datasetId) => api.get(`/alerts/dataset/${datasetId}/summary`),
  acknowledgeAlert: (alertId) => api.post(`/alerts/${alertId}/acknowledge`),

  // Reports
  getReport: (datasetId, format = 'text') =>
    api.get(`/datasets/${datasetId}/report`, { params: { format } }),

  // Health
  getHealth: () => api.get('/health'),
}

export default api
