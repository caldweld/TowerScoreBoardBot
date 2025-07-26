import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    https: true // Enable HTTPS for local development
  },
  define: {
    // Make environment variables available to the frontend
    'process.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://13.239.95.169:8000')
  }
})
