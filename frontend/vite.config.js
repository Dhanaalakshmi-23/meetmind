import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],

  server: {
    proxy: {
      '/api': {
        target: 'http://meetmind:8000',
        changeOrigin: true,
      },
      // Frappe desk (login page) — lets you log in from the same origin
      // (localhost:5173) so the session + CSRF cookies land on localhost
      '/app': {
        target: 'http://meetmind:8000',
        changeOrigin: true,
      },
      '/assets': {
        target: 'http://meetmind:8000',
        changeOrigin: true,
      },
    },
  },
})