import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// In dev, proxy /api and /ws to the FastAPI backend (default :16921).
const BACKEND = process.env.PST_BACKEND_URL ?? 'http://127.0.0.1:16921';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 16920,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true },
      '/ws': { target: BACKEND.replace('http', 'ws'), ws: true },
    },
  },
});
