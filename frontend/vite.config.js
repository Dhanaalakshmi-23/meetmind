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
    },
  },
})