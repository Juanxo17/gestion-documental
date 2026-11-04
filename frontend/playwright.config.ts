import { defineConfig, devices } from "@playwright/test";

const urlRemota = process.env.E2E_BASE_URL;
const PUERTO_FRONT = 3100;
const PUERTO_BACK = 8100;

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 70_000 },
  retries: 0,
  reporter: "list",
  use: {
    baseURL: urlRemota ?? `http://localhost:${PUERTO_FRONT}`,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: urlRemota
    ? undefined
    : [
        {
          command: `uv run uvicorn gestion_documental.api.main:app --port ${PUERTO_BACK}`,
          cwd: "..",
          url: `http://127.0.0.1:${PUERTO_BACK}/health`,
          reuseExistingServer: true,
          timeout: 120_000,
        },
        {
          command: `npm run start -- --port ${PUERTO_FRONT}`,
          url: `http://localhost:${PUERTO_FRONT}/login`,
          reuseExistingServer: true,
          timeout: 120_000,
          env: { BACKEND_URL: `http://127.0.0.1:${PUERTO_BACK}` },
        },
      ],
});
