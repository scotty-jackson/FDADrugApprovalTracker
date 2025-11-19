/**
 * API service layer for making HTTP requests to the backend.
 * Provides a centralized interface for all API calls.
 */
import axios from 'axios';
import config from '../config';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens, logging, etc.
api.interceptors.request.use(
  (config) => {
    // Could add auth tokens here if needed in the future
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Centralized error handling
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Drug API endpoints
 */
export const drugApi = {
  /**
   * Get paginated list of drugs with optional filters
   */
  getDrugs: (params = {}) => api.get('/drugs', { params }),

  /**
   * Get detailed information about a specific drug
   */
  getDrug: (id) => api.get(`/drugs/${id}`),

  /**
   * Get list of therapeutic areas for filters
   */
  getTherapeuticAreas: () => api.get('/drugs/therapeutic-areas/list'),
};

/**
 * Approval API endpoints
 */
export const approvalApi = {
  /**
   * Get paginated list of approvals with optional filters
   */
  getApprovals: (params = {}) => api.get('/approvals', { params }),

  /**
   * Get detailed information about a specific approval
   */
  getApproval: (id) => api.get(`/approvals/${id}`),
};

/**
 * Event API endpoints
 */
export const eventApi = {
  /**
   * Get paginated list of events with optional filters
   */
  getEvents: (params = {}) => api.get('/events', { params }),

  /**
   * Get upcoming events within specified days
   */
  getUpcomingEvents: (params = {}) => api.get('/events/upcoming', { params }),
};

/**
 * Summary/Dashboard API endpoints
 */
export const summaryApi = {
  /**
   * Get summary statistics for dashboard
   */
  getSummaryStats: () => api.get('/summary'),

  /**
   * Get list of all sponsors
   */
  getSponsors: () => api.get('/summary/sponsors'),
};

/**
 * Subscription API endpoints
 */
export const subscriptionApi = {
  /**
   * Subscribe to email notifications
   */
  subscribe: (email) => api.post('/subscriptions/subscribe', { email }),

  /**
   * Verify email with token
   */
  verifyEmail: (token) => api.get('/subscriptions/verify', { params: { token } }),

  /**
   * Subscribe to a specific drug
   */
  subscribeToDrug: (drugId, email) =>
    api.post(`/subscriptions/drugs/${drugId}`, null, { params: { email } }),

  /**
   * Unsubscribe from a specific drug
   */
  unsubscribeFromDrug: (drugId, email) =>
    api.delete(`/subscriptions/drugs/${drugId}`, { params: { email } }),

  /**
   * Get my drug subscriptions
   */
  getMySubscriptions: (email) =>
    api.get('/subscriptions/my-subscriptions', { params: { email } }),

  /**
   * Get subscription preferences
   */
  getPreferences: (email) =>
    api.get('/subscriptions/preferences', { params: { email } }),

  /**
   * Update subscription preferences
   */
  updatePreferences: (email, updates) =>
    api.patch('/subscriptions/preferences', updates, { params: { email } }),

  /**
   * Unsubscribe from all notifications
   */
  unsubscribeAll: (email) =>
    api.post('/subscriptions/unsubscribe-all', null, { params: { email } }),

  /**
   * Check if subscribed to a drug
   */
  checkSubscriptionStatus: (drugId, email) =>
    api.get(`/subscriptions/check/${drugId}`, { params: { email } }),
};

// Export default api instance for custom requests
export default api;
