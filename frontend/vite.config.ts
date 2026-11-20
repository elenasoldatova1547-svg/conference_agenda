import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// В dev-режиме проксируем API на backend (порт 8000), чтобы фронт обращался
// к относительным путям /api и /health без настройки CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
