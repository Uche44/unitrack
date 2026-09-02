import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), react()],
  esbuild: {
    drop: ["console", "debugger"],
  },
  test: {
    environment: "jsdom",
    globals: false,
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    env: {
      VITE_API_URL: "http://test.local",
    },
    environmentOptions: {
      jsdom: {
        url: "http://localhost/auth/login",
      },
    },
  },
});
