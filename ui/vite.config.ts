import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const DEV_SERVER_PORT = 1420;

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: { port: DEV_SERVER_PORT, strictPort: true },
  build: { target: "es2022" },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
