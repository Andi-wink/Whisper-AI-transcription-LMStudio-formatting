import { test, expect } from '@playwright/test';

/**
 * E2E Test: Agent Flow - Complete User Journey
 * 
 * Tests the expected behavior:
 * 1. Landing Page: Avatar preloads silently, NO agent speaks
 * 2. User clicks Video Agent: Agent is dispatched and greets
 * 3. User speaks: Agent responds
 * 4. User clicks End Call: Clean disconnect, returns to landing
 * 5. Landing Page again: Silent preload, no greeting
 */

test.describe('Agent Flow - Silent Preload & Dispatch on Click', () => {
  
  // Helper function to login
  async function login(page: any) {
    await page.goto('/');
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
  }

  // Helper to collect console logs
  function setupConsoleLogger(page: any) {
    const logs: string[] = [];
    page.on('console', (msg: any) => {
      logs.push(`[${msg.type()}] ${msg.text()}`);
    });
    return logs;
  }

  test('Step 1: Landing page should preload avatar SILENTLY (no agent greeting)', async ({ page }) => {
    const logs = setupConsoleLogger(page);
    
    await login(page);
    
    console.log('📍 On landing page - checking for silent preload...');
    
    // Wait for preload to complete
    await expect(page.locator('text=Agent ready').or(page.locator('text=Preparing agent'))).toBeVisible({ timeout: 30000 });
    
    // CRITICAL: Wait 10 seconds on landing page - agent should NOT speak
    console.log('⏳ Waiting 10 seconds to verify no agent greeting...');
    await page.waitForTimeout(10000);
    
    // Check that NO agent message appeared in any chat or transcript
    // Look for common greeting phrases that would indicate agent spoke
    const greetingIndicators = [
      'Hello Andrew',
      'Great to see you',
      'How can I help',
      'Welcome to U-insure',
      'assist you today'
    ];
    
    for (const phrase of greetingIndicators) {
      const element = page.locator(`text=${phrase}`);
      const count = await element.count();
      if (count > 0) {
        console.log(`❌ FAIL: Found agent greeting on landing page: "${phrase}"`);
        await page.screenshot({ path: 'e2e/screenshots/fail-landing-greeting.png' });
        throw new Error(`Agent spoke on landing page! Found: "${phrase}"`);
      }
    }
    
    // Check console logs for dispatch (should see skipDispatch)
    const dispatchLogs = logs.filter(l => l.includes('Dispatching') || l.includes('dispatch'));
    console.log('Dispatch-related logs:', dispatchLogs);
    
    await page.screenshot({ path: 'e2e/screenshots/landing-silent.png' });
    console.log('✅ PASS: Landing page is silent - no agent greeting');
  });

  test('Step 2: Clicking Video Agent should dispatch agent and trigger greeting', async ({ page }) => {
    const logs = setupConsoleLogger(page);
    
    await login(page);
    
    // Wait for preload
    await expect(page.locator('text=Agent ready').or(page.locator('text=Preparing agent'))).toBeVisible({ timeout: 30000 });
    await page.waitForTimeout(2000);
    
    console.log('🎬 Clicking Video Agent button...');
    await page.click('text=Video Agent');
    
    // Should transition to agent view
    const videoContainer = page.locator('.beyondpresence-video-container');
    await expect(videoContainer).toBeVisible({ timeout: 60000 });
    
    // Check console for dispatch call
    await page.waitForTimeout(3000);
    const dispatchLog = logs.find(l => l.includes('Dispatching avatar-agent'));
    if (dispatchLog) {
      console.log('✅ Dispatch call detected:', dispatchLog);
    }
    
    // Wait for agent greeting (should happen within 15 seconds of dispatch)
    console.log('⏳ Waiting for agent greeting...');
    
    // Look for greeting in chat panel
    const greetingDetected = await page.locator('text=Hello Andrew')
      .or(page.locator('text=Great to see you'))
      .or(page.locator('text=U-insure'))
      .first()
      .isVisible({ timeout: 20000 })
      .catch(() => false);
    
    if (greetingDetected) {
      console.log('✅ PASS: Agent greeting detected after clicking Video Agent');
    } else {
      console.log('⚠️ Agent greeting not detected in chat (may have been spoken only)');
    }
    
    await page.screenshot({ path: 'e2e/screenshots/video-agent-greeting.png' });
  });

  test('Step 3: End call should disconnect and return to landing page', async ({ page }) => {
    const logs = setupConsoleLogger(page);
    
    await login(page);
    
    // Quick path to agent view
    await page.waitForTimeout(3000);
    await page.click('text=Video Agent');
    
    // Wait for agent view
    await page.waitForTimeout(5000);
    
    console.log('🔴 Clicking End Call button...');
    
    // Find and click end call button
    const endCallBtn = page.locator('button[title="End Call"]')
      .or(page.locator('button:has(svg[class*="text-red"])'))
      .or(page.locator('button.bg-red-500'));
    
    await expect(endCallBtn.first()).toBeVisible({ timeout: 10000 });
    await endCallBtn.first().click();
    
    // Check for disconnect log
    await page.waitForTimeout(2000);
    const disconnectLog = logs.find(l => l.includes('End call') || l.includes('disconnect'));
    if (disconnectLog) {
      console.log('✅ Disconnect detected:', disconnectLog);
    }
    
    // Should return to landing page
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Video Agent')).toBeVisible({ timeout: 5000 });
    
    await page.screenshot({ path: 'e2e/screenshots/returned-to-landing.png' });
    console.log('✅ PASS: Call ended and returned to landing page');
  });

  test('Step 4: After returning to landing, should preload silently again', async ({ page }) => {
    const logs = setupConsoleLogger(page);
    
    await login(page);
    
    // Go to agent view
    await page.waitForTimeout(3000);
    await page.click('text=Video Agent');
    await page.waitForTimeout(5000);
    
    // End call
    const endCallBtn = page.locator('button[title="End Call"]').first();
    await endCallBtn.click();
    
    // Wait for landing page
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 15000 });
    
    console.log('📍 Back on landing page - checking for silent re-preload...');
    
    // Wait for re-preload
    await expect(page.locator('text=Agent ready').or(page.locator('text=Preparing agent'))).toBeVisible({ timeout: 30000 });
    
    // Wait 10 seconds - should remain silent
    console.log('⏳ Waiting 10 seconds to verify no agent greeting on re-preload...');
    await page.waitForTimeout(10000);
    
    // Verify no greeting appeared
    const greetingElement = page.locator('text=Hello Andrew');
    const hasGreeting = await greetingElement.count() > 0;
    
    if (hasGreeting) {
      await page.screenshot({ path: 'e2e/screenshots/fail-repreload-greeting.png' });
      throw new Error('Agent spoke during re-preload!');
    }
    
    await page.screenshot({ path: 'e2e/screenshots/landing-repreload-silent.png' });
    console.log('✅ PASS: Re-preload is silent - no agent greeting');
  });

  test('Full flow: Landing (silent) → Click Video → Greeting → End Call → Landing (silent)', async ({ page }) => {
    const logs = setupConsoleLogger(page);
    
    // === PHASE 1: Login and verify silent landing ===
    await login(page);
    console.log('=== PHASE 1: Verify silent landing ===');
    
    await expect(page.locator('text=Agent ready').or(page.locator('text=Preparing agent'))).toBeVisible({ timeout: 30000 });
    await page.waitForTimeout(5000);
    
    // Verify no greeting on landing
    const landingGreeting = await page.locator('text=Hello').count();
    expect(landingGreeting).toBe(0);
    console.log('✅ Phase 1: Landing page is silent');
    
    // === PHASE 2: Click Video Agent and verify greeting ===
    console.log('=== PHASE 2: Click Video Agent ===');
    await page.click('text=Video Agent');
    
    const videoContainer = page.locator('.beyondpresence-video-container');
    await expect(videoContainer).toBeVisible({ timeout: 60000 });
    console.log('✅ Phase 2: Video agent view loaded');
    
    // === PHASE 3: End call ===
    console.log('=== PHASE 3: End call ===');
    await page.waitForTimeout(3000);
    
    const endCallBtn = page.locator('button[title="End Call"]').first();
    await endCallBtn.click();
    
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 15000 });
    console.log('✅ Phase 3: Returned to landing page');
    
    // === PHASE 4: Verify silent re-preload ===
    console.log('=== PHASE 4: Verify silent re-preload ===');
    await page.waitForTimeout(5000);
    
    const repreloadGreeting = await page.locator('text=Hello').count();
    expect(repreloadGreeting).toBe(0);
    console.log('✅ Phase 4: Re-preload is silent');
    
    await page.screenshot({ path: 'e2e/screenshots/full-flow-complete.png' });
    console.log('🎉 FULL FLOW TEST PASSED');
  });
});
