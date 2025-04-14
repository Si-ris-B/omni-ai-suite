import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path'; // Make sure to install path: npm i -D path

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174, // Try a different port
    strictPort: true, // Optional: Fail if port is busy
    host: true // Optional: Accessible on network IP
  },
  resolve: {
    alias: {
      // This line maps '@/' to your 'src/' directory
      '@': path.resolve(__dirname, './src'),
    },
  },
});