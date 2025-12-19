import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Run tests sequentially for avatar tests
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker for sequential execution
  reporter: 'html',
  timeout: 120000, // 2 minutes per test (avatar loading can be slow)
  
  use: {
    baseURL: 'http://localhost:3001',
    trace: 'on-first-retry',
    video: 'on', // Record video for debugging
    screenshot: 'on',
    
    // Grant permissions for microphone/camera
    permissions: ['microphone', 'camera'],
    
    // Use a consistent viewport
    viewport: { width: 1280, height: 720 },
  },

  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: [
            '--use-fake-ui-for-media-stream', // Auto-accept mic/camera permissions
            '--use-fake-device-for-media-stream', // Use fake audio/video
            '--autoplay-policy=no-user-gesture-required', // Allow autoplay
          ],
        },
      },
    },
  ],

  // Run local dev server before tests
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3001',
    reuseExistingServer: true, // Reuse existing server
    timeout: 120000, // 2 minutes to start server
  },
});
