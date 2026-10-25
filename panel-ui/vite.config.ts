import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const BACKEND = 'http://127.0.0.1:47810'

export default defineConfig({
  base: '/panel-next/',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5178,
    strictPort: true,
    proxy: {
      '/state': BACKEND,
      '/rpc': BACKEND,
      '/peaks': BACKEND,
      '/audio': BACKEND,
      '/doc': BACKEND,
      '/upload': BACKEND,
      '/panel/icon.png': BACKEND,
      '/panel/mictest.wav': BACKEND,
    },
  },
  build: { outDir: '../panel-next', emptyOutDir: true },
})
