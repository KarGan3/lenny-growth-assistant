import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// The frontend talks to the backend under /api. In dev we proxy that to the
// FastAPI server so there are no CORS headaches and the code needs no base URL.
// In prod (Docker) nginx proxies /api to the backend container (see nginx.conf).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api(?=\/|$)/, ''),
      },
    },
  },
  }
})
