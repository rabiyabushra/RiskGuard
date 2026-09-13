import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // System Health
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Projects
  getProjects: async ({ page = 1, limit = 50, state = '', sector = '', risk_category = '' } = {}) => {
    const params = { page, limit };
    if (state) params.state = state;
    if (sector) params.sector = sector;
    if (risk_category) params.risk_category = risk_category;

    const res = await apiClient.get('/projects', { params });
    return res.data;
  },

  getProjectById: async (projectId) => {
    const res = await apiClient.get(`/projects/${projectId}`);
    return res.data;
  },

  createProject: async (projectData) => {
    const res = await apiClient.post('/projects', projectData);
    return res.data;
  },

  // Real ML Prediction
  predictDelay: async (projectData) => {
    const res = await apiClient.post('/predict', projectData);
    return res.data;
  },

  // Risk Analysis
  getRiskAnalysis: async (projectId) => {
    const res = await apiClient.get(`/risk-analysis/${projectId}`);
    return res.data;
  },

  analyzeCustomRisk: async (projectData) => {
    const res = await apiClient.post('/risk-analysis', projectData);
    return res.data;
  },

  getCustomRecommendations: async (projectData, customContext = null) => {
    const res = await apiClient.post('/recommendations', {
      project_data: projectData,
      custom_context: customContext,
    });
    return res.data;
  },

  // SHAP Explainability
  getProjectExplanation: async (projectId) => {
    const res = await apiClient.get(`/projects/${projectId}/explanation`);
    return res.data;
  },

  getGlobalSHAP: async (topN = 15) => {
    const res = await apiClient.get('/shap/global', { params: { top_n: topN } });
    return res.data;
  },

  explainCustomProject: async (projectData, topN = 5) => {
    const res = await apiClient.post('/shap/explain', projectData, { params: { top_n: topN } });
    return res.data;
  },

  // Gemini Recommendations
  getRecommendations: async (payload) => {
    const res = await apiClient.post('/recommendations', payload);
    return res.data;
  },

  getProjectRecommendations: async (projectId) => {
    const res = await apiClient.get(`/projects/${projectId}/recommendations`);
    return res.data;
  },
};

export default api;
