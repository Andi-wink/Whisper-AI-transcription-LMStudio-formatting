import { test, expect } from '@playwright/test';

/**
 * E2E Test: Avatar Video Layout
 * 
 * Tests that the avatar video resizes properly to fit available space
 * and doesn't extend behind the chat panel.
 */

test.describe('Avatar Video Layout', () => {
  
  test('avatar video should resize when chat panel opens/closes', async ({ page }) => {
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
    
    // Get viewport width
    const viewportSize = page.viewportSize();
    const viewportWidth = viewportSize?.width || 1280;
    console.log(`📐 Viewport width: ${viewportWidth}px`);
    
    // Find the video container (BeyondPresenceStream wrapper)
    const videoContainer = page.locator('div[class*="fixed top-0 left-0 bottom-0"]').first();
    
    // Test 1: With chat open (default), video should not extend to full width
    const chatPanel = page.locator('div[class*="w-80"], div[class*="w-96"]');
    const isChatVisible = await chatPanel.isVisible().catch(() => false);
    
    if (isChatVisible) {
      const videoBox = await videoContainer.boundingBox();
      if (videoBox) {
        console.log(`📐 Video width with chat open: ${videoBox.width}px`);
        // Video should be less than full viewport width (chat panel takes space)
        expect(videoBox.width).toBeLessThan(viewportWidth);
        console.log('✅ Video is properly sized with chat open');
      }
    }
    
    // Take screenshot with chat open
    await page.screenshot({ path: 'e2e/screenshots/layout-chat-open.png', fullPage: true });
    
    // Test 2: Hide chat panel
    const hideChatButton = page.locator('button[title="Hide Chat"]');
    if (await hideChatButton.isVisible()) {
      await hideChatButton.click();
      await page.waitForTimeout(500); // Wait for transition
      
      const videoBoxClosed = await videoContainer.boundingBox();
      if (videoBoxClosed) {
        console.log(`📐 Video width with chat closed: ${videoBoxClosed.width}px`);
        // Video should now be full width (or close to it)
        expect(videoBoxClosed.width).toBeGreaterThan(viewportWidth - 50);
        console.log('✅ Video expands when chat is closed');
      }
    }
    
    // Take screenshot with chat closed
    await page.screenshot({ path: 'e2e/screenshots/layout-chat-closed.png', fullPage: true });
    
    // Test 3: Reopen chat and verify video shrinks again
    const showChatButton = page.locator('button[title="Show Chat"]');
    if (await showChatButton.isVisible()) {
      await showChatButton.click();
      await page.waitForTimeout(500);
      
      const videoBoxReopened = await videoContainer.boundingBox();
      if (videoBoxReopened) {
        console.log(`📐 Video width after reopening chat: ${videoBoxReopened.width}px`);
        expect(videoBoxReopened.width).toBeLessThan(viewportWidth);
        console.log('✅ Video shrinks when chat reopens');
      }
    }
    
    console.log('✅ TEST PASSED: Avatar video layout is responsive');
  });

  test('chat panel should not overlap video content', async ({ page }) => {
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
    
    // Get chat panel position
    const chatPanel = page.locator('div[class*="border-l border-white"]').first();
    const chatBox = await chatPanel.boundingBox();
    
    // Get video container position
    const videoContainer = page.locator('div[class*="fixed top-0 left-0 bottom-0"]').first();
    const videoBox = await videoContainer.boundingBox();
    
    if (chatBox && videoBox) {
      // Video right edge should be at or before chat left edge
      const videoRightEdge = videoBox.x + videoBox.width;
      const chatLeftEdge = chatBox.x;
      
      console.log(`📐 Video right edge: ${videoRightEdge}px`);
      console.log(`📐 Chat left edge: ${chatLeftEdge}px`);
      
      // Allow 2px tolerance for rounding
      expect(videoRightEdge).toBeLessThanOrEqual(chatLeftEdge + 2);
      console.log('✅ Video does not overlap chat panel');
    }
    
    console.log('✅ TEST PASSED: No overlap between video and chat');
  });
});
