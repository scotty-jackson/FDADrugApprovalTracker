/**
 * Frontend configuration
 * Reads from environment variables with fallbacks for development
 */

const config = {
  // API base URL - uses environment variable or defaults to localhost for development
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',

  // Application settings
  app: {
    name: 'FDA Drug Approval Tracker',
    version: '1.0.0',
  },

  // Pagination defaults
  pagination: {
    defaultPageSize: 20,
    pageSizeOptions: [10, 20, 50, 100],
  },
};

export default config;
