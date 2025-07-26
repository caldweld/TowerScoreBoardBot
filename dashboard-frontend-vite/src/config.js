// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://www.toweraus.com:8000';

// API Endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/api/auth/login`,
    LOGOUT: `${API_BASE_URL}/api/auth/logout`,
    ME: `${API_BASE_URL}/api/auth/me`,
  },
  ADMIN: {
    BOT_ADMINS: `${API_BASE_URL}/api/admin/bot-admins`,
    ADD_BOT_ADMIN: `${API_BASE_URL}/api/admin/add-bot-admin`,
    REMOVE_BOT_ADMIN: `${API_BASE_URL}/api/admin/remove-bot-admin`,
  },
  LEADERBOARD: {
    WAVE: `${API_BASE_URL}/api/leaderboard/wave`,
    COINS: `${API_BASE_URL}/api/leaderboard/coins`,
    TIER: (tier) => `${API_BASE_URL}/api/leaderboard/tier/${tier}`,
  },
  STATS: {
    OVERVIEW: `${API_BASE_URL}/api/stats/overview`,
    LEADERBOARD: (field) => `${API_BASE_URL}/api/stats-leaderboard?field=${field}`,
  },
  USER: {
    PROGRESS: (tier) => `${API_BASE_URL}/api/user/progress?tier=${tier}`,
    ALL: `${API_BASE_URL}/api/users`,
  },
  EXPORT: (format) => `${API_BASE_URL}/api/export/${format}`,
}; 