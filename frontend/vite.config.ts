import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@components': resolve(__dirname, './src/shared/components'),
      '@hooks': resolve(__dirname, './src/shared/hooks'),
      '@lib': resolve(__dirname, './src/shared/lib'),
      '@types': resolve(__dirname, './src/shared/types'),
      '@features': resolve(__dirname, './src/features'),
      '@app': resolve(__dirname, './src/app'),
      '@styles': resolve(__dirname, './src/styles'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
