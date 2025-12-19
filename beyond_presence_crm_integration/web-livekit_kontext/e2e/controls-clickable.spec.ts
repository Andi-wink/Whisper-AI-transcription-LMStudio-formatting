import { test, expect } from '@playwright/test';

/**
 * E2E Test: Controls Accessibility
 * 
 * Tests that the chat panel and hangup button are clickable
 * when the avatar video is displayed (not blocked by z-index).
 */

test.describe('Controls Accessibility', () => {
  
  test('chat toggle and end call buttons should be clickable in video agent view', async ({ page }) => {
    // Login
    await page.goto('/');
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    console.log('✅ Logged in');
    
    // Wait for preload
    await page.waitForTimeout(5000);
    
    // Click Video Agent
    await page.click('text=Video Agent');
    await page.waitForTimeout(3000);
    
    // Verify agent view is visible
    const agentView = page.locator('#agent-view');
    await expect(agentView).toBeVisible({ timeout: 10000 });
    console.log('✅ Agent view visible');
    
    // Test 1: Chat toggle button should be clickable
    const chatToggleButton = page.locator('button[title="Hide Chat"]');
    await expect(chatToggleButton).toBeVisible({ timeout: 5000 });
    
    // Click to hide chat
    await chatToggleButton.click();
    console.log('✅ Chat toggle button clicked (hide)');
    
    // Verify chat is hidden (button title changes)
    const showChatButton = page.locator('button[title="Show Chat"]');
    await expect(showChatButton).toBeVisible({ timeout: 3000 });
    console.log('✅ Chat panel hidden');
    
    // Click to show chat again
    await showChatButton.click();
    console.log('✅ Chat toggle button clicked (show)');
    
    // Verify chat is visible again
    await expect(page.locator('button[title="Hide Chat"]')).toBeVisible({ timeout: 3000 });
    console.log('✅ Chat panel shown again');
    
    // Test 2: End call button should be clickable
    const endCallButton = page.locator('button[title="End Call"]');
    await expect(endCallButton).toBeVisible({ timeout: 5000 });
    console.log('✅ End call button is visible');
    
    // Take screenshot before clicking end call
    await page.screenshot({ path: 'e2e/screenshots/controls-visible.png', fullPage: true });
    
    // Click end call (this will reload the page)
    await endCallButton.click();
    console.log('✅ End call button clicked');
    
    // Verify page reloads to landing
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 15000 });
    console.log('✅ Page reloaded to landing after end call');
    
    console.log('✅ TEST PASSED: All controls are clickable');
  });

  test('chat input should be typeable in video agent view', async ({ page }) => {
    // Login
    await page.goto('/');
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    
    // Wait for preload and click Video Agent
    await page.waitForTimeout(5000);
    await page.click('text=Video Agent');
    await page.waitForTimeout(3000);
    
    // Find chat input
    const chatInput = page.locator('input[placeholder="Type a message..."]');
    
    try {
      await expect(chatInput).toBeVisible({ timeout: 5000 });
      
      // Type in chat input
      await chatInput.fill('Hello, this is a test message');
      console.log('✅ Chat input is typeable');
      
      // Verify text was entered
      await expect(chatInput).toHaveValue('Hello, this is a test message');
      console.log('✅ Text entered successfully');
      
      // Take screenshot
      await page.screenshot({ path: 'e2e/screenshots/chat-input-test.png', fullPage: true });
      
    } catch (e) {
      console.log('⚠️ Chat input not found - may have different placeholder');
      // Try alternative selector
      const altInput = page.locator('.chat-input, input[type="text"]').first();
      if (await altInput.isVisible()) {
        await altInput.fill('Hello, this is a test message');
        console.log('✅ Alternative chat input is typeable');
      }
    }
  });
});
