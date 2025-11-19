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

// Export default api instance for custom requests
export default api;
