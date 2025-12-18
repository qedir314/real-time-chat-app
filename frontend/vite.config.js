import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/signin': 'http://localhost:8000',
      '/signup': 'http://localhost:8000',
      '/me': 'http://localhost:8000',
      '/history': 'http://localhost:8000',
      '/rooms': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
