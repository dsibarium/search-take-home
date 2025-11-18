import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const BASE_URL = "http://localhost:8000";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: BASE_URL,
        changeOrigin: false,
        secure: false,
      },
    },
  },
});
