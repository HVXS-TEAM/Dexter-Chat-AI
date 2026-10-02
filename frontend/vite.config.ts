import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Port deja autorise par le CORS du backend (app/main.py) : evite tout blocage en dev.
    port: 4173,
    strictPort: true,
  },
})
