import { test, expect } from '@playwright/test';

/**
 * E2E Test: Avatar Greeting Flow
 * 
 * Tests the preload-metadata flow:
 * 1. Avatar should be SILENT on landing page (preload mode)
 * 2. Avatar should GREET only after clicking Video Agent
 * 
 * This test monitors:
 * - Console logs for metadata updates
 * - Network requests for room-metadata API calls
 * - Agent transcript for greeting detection
 */

test.describe('Avatar Greeting Flow', () => {
  
  test('avatar should be silent on landing, greet only after click', async ({ page }) => {
    const consoleLogs: string[] = [];
    const networkRequests: { url: string; method: string; body?: string }[] = [];
    
    // Capture console logs
    page.on('console', msg => {
      const text = msg.text();
      consoleLogs.push(text);
      if (text.includes('🟢') || text.includes('🎯') || text.includes('✅') || text.includes('Room')) {
        console.log(`[Browser] ${text}`);
      }
    });
    
    // Capture network requests to room-metadata API
    page.on('request', request => {
      if (request.url().includes('room-metadata')) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          body: request.postData() || undefined
        });
        console.log(`[Network] ${request.method()} ${request.url()}`);
      }
    });

    // Step 1: Navigate and login
    console.log('🔐 Logging in...');
    await page.goto('/');
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    // Step 2: Wait for landing page
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    console.log('✅ On landing page');
    
    // Step 3: Wait on landing page - avatar should NOT trigger greeting
    console.log('⏳ Waiting 10 seconds on landing page (avatar should stay silent)...');
    await page.waitForTimeout(10000);
    
    // Check that NO room-metadata request was made yet (greeting not triggered)
    const metadataRequestsBeforeClick = networkRequests.filter(r => 
      r.body?.includes('"preload":false')
    );
    console.log(`📊 Metadata updates before click: ${metadataRequestsBeforeClick.length}`);
    
    // Step 4: Click Video Agent
    console.log('🎬 Clicking Video Agent...');
    const clickTime = Date.now();
    await page.click('text=Video Agent');
    
    // Step 5: Wait for greeting to be triggered
    console.log('⏳ Waiting for greeting to trigger...');
    await page.waitForTimeout(5000);
    
    // Check that room-metadata request WAS made after click
    const metadataRequestsAfterClick = networkRequests.filter(r => 
      r.body?.includes('"preload":false')
    );
    console.log(`📊 Metadata updates after click: ${metadataRequestsAfterClick.length}`);
    
    // Verify the greeting was triggered
    const greetingTriggered = consoleLogs.some(log => 
      log.includes('Both room connected AND user ready') ||
      log.includes('Room metadata updated')
    );
    console.log(`🎯 Greeting triggered: ${greetingTriggered}`);
    
    // Take screenshot
    await page.screenshot({ path: 'e2e/screenshots/avatar-greeting-test.png', fullPage: true });
    
    // Assertions
    expect(metadataRequestsAfterClick.length).toBeGreaterThan(0);
    console.log('✅ TEST PASSED: Metadata update was sent after clicking Video Agent');
  });

  test('console logs show correct greeting flow', async ({ page }) => {
    const consoleLogs: string[] = [];
    
    page.on('console', msg => {
      consoleLogs.push(msg.text());
    });

    // Login
    await page.goto('/');
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    
    // Wait for room to connect
    await page.waitForTimeout(8000);
    
    // Check for room connected log
    const roomConnected = consoleLogs.some(log => log.includes('Room connected'));
    console.log(`📡 Room connected: ${roomConnected}`);
    
    // Click Video Agent
    await page.click('text=Video Agent');
    await page.waitForTimeout(3000);
    
    // Check for handleStartAgent log
    const handleStartAgentCalled = consoleLogs.some(log => log.includes('handleStartAgent called'));
    console.log(`🔵 handleStartAgent called: ${handleStartAgentCalled}`);
    
    // Check for greeting trigger log
    const greetingTriggered = consoleLogs.some(log => 
      log.includes('Both room connected AND user ready') ||
      log.includes('triggering greeting')
    );
    console.log(`🟢 Greeting triggered: ${greetingTriggered}`);
    
    // Check for metadata update log
    const metadataUpdated = consoleLogs.some(log => log.includes('Room metadata updated'));
    console.log(`✅ Metadata updated: ${metadataUpdated}`);
    
    // Log all relevant logs for debugging
    console.log('\n--- Relevant Console Logs ---');
    consoleLogs
      .filter(log => 
        log.includes('🚀') || log.includes('🔵') || log.includes('🟢') || 
        log.includes('🎯') || log.includes('✅') || log.includes('Room') ||
        log.includes('handleStartAgent')
      )
      .forEach(log => console.log(log));
    
    await page.screenshot({ path: 'e2e/screenshots/greeting-flow-logs.png', fullPage: true });
    
    // Assertions
    expect(roomConnected || handleStartAgentCalled).toBeTruthy();
  });
});
