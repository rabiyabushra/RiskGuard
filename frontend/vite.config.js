import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@gis': path.resolve(__dirname, '../gis')
    }
  },
  server: {
    port: 3000,
    fs: {
      allow: ['..']
    }
  }
});
