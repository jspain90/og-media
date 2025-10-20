import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    host: '0.0.0.0',  // Allow external connections for Cloudflare tunnel
    allowedHosts: [
      'media.galahad.cc',
      '.galahad.cc'  // Allow all subdomains
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      }
    }
  },
  preview: {
    port: 5175,
    host: '0.0.0.0',  // Allow external connections for Cloudflare tunnel
    allowedHosts: [
      'media.galahad.cc',
      '.galahad.cc'  // Allow all subdomains
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      }
    }
  }
})
