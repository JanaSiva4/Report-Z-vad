import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        headers: {
          "X-Goog-Authenticated-User-Email": "accounts.google.com:dev@alza.cz"
        }
      }
    }
  }
});
