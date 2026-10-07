import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const DEV_SERVER_PORT = 1420;

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: { port: DEV_SERVER_PORT, strictPort: true },
  build: { target: "es2022" },
  test: {
    projects: [
      {
        extends: true,
        test: { name: "node", environment: "node", include: ["src/**/*.test.ts"] },
      },
      {
        extends: true,
        test: {
          name: "dom",
          environment: "jsdom",
          include: ["src/**/*.test.tsx"],
          setupFiles: ["src/test/setup-dom.ts"],
        },
      },
    ],
  },
});
