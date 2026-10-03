import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import Cookies from 'js-cookie';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request Interceptor: Attach Access Token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Auto Refresh Token on 401
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (typeof window === 'undefined') {
        return Promise.reject(error);
      }

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken || originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/auth/login')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(`${API_BASE}/api/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: newRefreshToken } = response.data;
        localStorage.setItem('access_token', access_token);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }

        api.defaults.headers.common.Authorization = `Bearer ${access_token}`;
        processQueue(null, access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// Agentic Platform API Client Helpers
export const AgenticAPI = {
  // Human Review Operations
  getHumanReviews: async (status?: string) => {
    const params = status ? { status } : {};
    const res = await api.get('/human-reviews', { params });
    return res.data;
  },
  approveHumanReview: async (reviewId: number, comments: string, modifications?: any) => {
    const res = await api.post(`/human-reviews/${reviewId}/approve`, { comments, modifications });
    return res.data;
  },
  rejectHumanReview: async (reviewId: number, comments: string) => {
    const res = await api.post(`/human-reviews/${reviewId}/reject`, { comments });
    return res.data;
  },
  escalateHumanReview: async (reviewId: number, reason: string) => {
    const res = await api.post(`/human-reviews/${reviewId}/escalate`, { reason });
    return res.data;
  },

  // Patient 360 & Longitudinal Timeline
  getPatient360: async (patientId: number | string) => {
    const res = await api.get(`/patients/${patientId}/360`);
    return res.data;
  },
  getPatientTimeline: async (patientId: number | string) => {
    const res = await api.get(`/patients/${patientId}/timeline`);
    return res.data;
  },
  getPatientLabTrends: async (patientId: number | string) => {
    const res = await api.get(`/patients/${patientId}/labs/trends`);
    return res.data;
  },

  // Healthcare Data Analyst (DuckDB)
  queryAnalytics: async (query: string, chart_type?: string, parameters?: any) => {
    const res = await api.post('/analytics/query', { query, chart_type, parameters });
    return res.data;
  },
  getAnalyticsProfile: async () => {
    const res = await api.get('/analytics/profile');
    return res.data;
  },

  // Agent Operations Monitor
  getAgentMonitorStats: async () => {
    const res = await api.get('/agent-monitor');
    return res.data;
  },

  // Workflows
  getWorkflows: async (params?: { patient_id?: number; status?: string; limit?: number }) => {
    const res = await api.get('/workflows', { params });
    return res.data;
  },
  getWorkflowById: async (workflowId: string) => {
    const res = await api.get(`/workflows/${workflowId}`);
    return res.data;
  },
  cancelWorkflow: async (workflowId: string, reason?: string) => {
    const res = await api.post(`/workflows/${workflowId}/cancel`, { reason });
    return res.data;
  },
};

export default api;

