import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? "http://gateway";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@app": path.resolve(__dirname, "src/app"),
      "@pages": path.resolve(__dirname, "src/pages"),
      "@entities": path.resolve(__dirname, "src/entities"),
      "@shared": path.resolve(__dirname, "src/shared"),
      "@features": path.resolve(__dirname, "src/features"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }

          if (id.includes("node_modules/react-router") || id.includes("node_modules/@remix-run")) {
            return "vendor-router";
          }

          if (
            id.includes("node_modules/react") ||
            id.includes("node_modules/scheduler") ||
            id.includes("node_modules/@mui") ||
            id.includes("node_modules/@emotion")
          ) {
            return "vendor-framework";
          }

          if (id.includes("node_modules/react-hook-form") || id.includes("node_modules/@hookform") || id.includes("node_modules/zod")) {
            return "vendor-forms";
          }

          return undefined;
        },
      },
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
