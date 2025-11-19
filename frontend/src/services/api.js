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

/**
 * Clinical Trials API endpoints
 */
export const trialsApi = {
  /**
   * Get paginated list of trials with optional filters
   */
  getTrials: (params = {}) => api.get('/trials', { params }),

  /**
   * Get detailed information about a specific trial
   */
  getTrial: (id) => api.get(`/trials/${id}`),

  /**
   * Get trial by registry ID (e.g., NCT number)
   */
  getTrialByRegistryId: (registryId) => api.get(`/trials/registry/${registryId}`),

  /**
   * Get trials filtered by phase
   */
  getTrialsByPhase: (phase, params = {}) => api.get(`/trials/phase/${phase}`, { params }),
};

/**
 * Company API endpoints
 */
export const companyApi = {
  /**
   * Get list of all companies
   */
  getCompanies: (params = {}) => api.get('/companies', { params }),

  /**
   * Get company statistics and pipeline overview
   */
  getCompanyStats: (id) => api.get(`/companies/${id}/stats`),

  /**
   * Get trials for a specific company
   */
  getCompanyTrials: (id, params = {}) => api.get(`/companies/${id}/trials`, { params }),

  /**
   * Get drugs for a specific company
   */
  getCompanyDrugs: (id, params = {}) => api.get(`/companies/${id}/drugs`, { params }),
};

/**
 * Catalyst API endpoints
 */
export const catalystApi = {
  /**
   * Get paginated list of catalysts with optional filters
   */
  getCatalysts: (params = {}) => api.get('/catalysts', { params }),

  /**
   * Get upcoming catalysts grouped by month
   */
  getUpcomingCatalysts: (params = {}) => api.get('/catalysts/upcoming', { params }),

  /**
   * Get catalyst statistics
   */
  getCatalystStats: () => api.get('/catalysts/stats'),
};

/**
 * Disease Area API endpoints
 */
export const diseaseAreaApi = {
  /**
   * Get list of all disease areas
   */
  getDiseaseAreas: () => api.get('/disease-areas'),

  /**
   * Get statistics for a specific disease area
   */
  getDiseaseAreaStats: (diseaseArea) => api.get(`/disease-areas/${encodeURIComponent(diseaseArea)}/stats`),
};

// Export default api instance for custom requests
export default api;
