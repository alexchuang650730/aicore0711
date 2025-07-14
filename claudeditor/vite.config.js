import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: '.',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'monaco-editor': ['monaco-editor'],
          'react-vendor': ['react', 'react-dom'],
        },
      },
    },
  },
  server: {
    port: 5175,
    host: '127.0.0.1',
    strictPort: true,
  },
  optimizeDeps: {
    include: ['monaco-editor', '@tauri-apps/api'],
  },
  define: {
    global: 'globalThis',
  },
  clearScreen: false,
  envPrefix: ['VITE_', 'TAURI_'],
})