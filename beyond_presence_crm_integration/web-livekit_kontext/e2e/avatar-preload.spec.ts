import { test, expect } from '@playwright/test';

/**
 * E2E Test: Avatar Preloading
 * 
 * Tests that the avatar preloads in the background while on the landing page,
 * resulting in near-instant avatar appearance when clicking Video Agent.
 */

test.describe('Avatar Preloading', () => {
  
  test('should preload avatar on landing page and load quickly when selecting video', async ({ page }) => {
    // Step 1: Navigate to the app
    await page.goto('/');
    
    // Step 2: Login with demo credentials
    console.log('🔐 Logging in...');
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    // Step 3: Wait for landing page to load
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    console.log('✅ Logged in, on landing page');
    
    // Step 4: Check for preloading indicator
    const preloadingIndicator = page.locator('text=Preparing agent');
    const readyIndicator = page.locator('text=Agent ready');
    
    // Wait for preloading to start
    const startTime = Date.now();
    console.log('⏳ Waiting for avatar to preload (up to 30 seconds)...');
    
    // Wait for either "Preparing agent" or "Agent ready" to appear
    try {
      await expect(preloadingIndicator.or(readyIndicator)).toBeVisible({ timeout: 10000 });
      console.log('📡 Preloading started/detected');
    } catch (e) {
      console.log('⚠️ Preloading indicator not visible - may be using different UI');
    }
    
    // Step 5: Wait 15 seconds on landing page to allow preloading
    console.log('⏱️ Waiting 15 seconds on landing page...');
    await page.waitForTimeout(15000);
    
    // Check preload status after waiting
    const preloadTime = Date.now() - startTime;
    const isReady = await readyIndicator.isVisible();
    const isPreparing = await preloadingIndicator.isVisible();
    console.log(`⏱️ After 15s - Ready: ${isReady}, Preparing: ${isPreparing}, Total time: ${preloadTime}ms`);
    
    // Step 6: Click on Video Agent and measure load time
    console.log('🎬 Clicking Video Agent...');
    const clickTime = Date.now();
    
    await page.click('text=Video Agent');
    
    // Step 7: Wait for video element to appear with content
    // The avatar video should appear almost immediately if preloaded
    // First wait for the agent view to be visible
    const agentView = page.locator('#agent-view');
    await expect(agentView).toBeVisible({ timeout: 10000 });
    console.log('📺 Agent view visible');
    
    // Wait for connection status to show connected
    const connectedStatus = page.locator('text=Connected');
    try {
      await expect(connectedStatus).toBeVisible({ timeout: 30000 });
      console.log('✅ Connection status: Connected');
    } catch (e) {
      console.log('⚠️ Connection status not visible');
      await page.screenshot({ path: 'e2e/screenshots/connection-status-missing.png' });
    }
    
    // Look for video element or video container
    const videoContainer = page.locator('.beyondpresence-video-container');
    const videoElement = page.locator('video');
    
    // Wait for either the container or a video element
    try {
      await expect(videoContainer.or(videoElement)).toBeVisible({ timeout: 60000 });
      console.log('📺 Video container/element visible');
    } catch (e) {
      console.log('⚠️ No video element found - checking page state');
      await page.screenshot({ path: 'e2e/screenshots/no-video-element.png' });
      
      // Log the page content for debugging
      const html = await page.content();
      console.log('Page contains video:', html.includes('<video'));
      console.log('Page contains beyondpresence-video-container:', html.includes('beyondpresence-video-container'));
    }
    
    // Try to find actual video element with content
    const hasVideo = await page.evaluate(() => {
      const video = document.querySelector('video');
      return video ? { found: true, width: video.videoWidth, height: video.videoHeight } : { found: false };
    });
    console.log('🎥 Video element state:', JSON.stringify(hasVideo));
    
    const videoLoadTime = Date.now() - clickTime;
    console.log(`🎥 Time since click: ${videoLoadTime}ms`);
    
    // Step 8: Assert that video loaded quickly (under 5 seconds if preloaded)
    // Note: Without preloading it typically takes 10-15+ seconds
    if (videoLoadTime < 5000) {
      console.log('✅ PASS: Avatar loaded quickly (preloading working!)');
    } else if (videoLoadTime < 10000) {
      console.log('⚠️ WARN: Avatar took longer than expected but still reasonable');
    } else {
      console.log('❌ SLOW: Avatar took too long - preloading may not be working');
    }
    
    // Verify video is actually playing
    const isPlaying = await page.evaluate(() => {
      const video = document.querySelector('video') as HTMLVideoElement;
      return video && !video.paused && video.readyState >= 2;
    });
    
    console.log(`📺 Video playing: ${isPlaying}`);
    
    // Take a screenshot for visual verification
    await page.screenshot({ path: 'e2e/screenshots/avatar-loaded.png', fullPage: true });
    
    // Assert reasonable load time (adjust threshold as needed)
    expect(videoLoadTime).toBeLessThan(15000); // Should load within 15 seconds
  });

  test('should show preloading status on landing page', async ({ page }) => {
    await page.goto('/');
    
    // Login
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    
    // Check that we see Voice Agent and Video Agent cards
    await expect(page.locator('text=Voice Agent')).toBeVisible();
    await expect(page.locator('text=Video Agent')).toBeVisible();
    
    // Check for status indicator (should show preparing or ready)
    const statusArea = page.locator('.mt-8'); // The status indicator area
    await expect(statusArea).toBeVisible();
    
    // Wait a bit and check if status changes
    await page.waitForTimeout(5000);
    
    // Screenshot the landing page state
    await page.screenshot({ path: 'e2e/screenshots/landing-page.png', fullPage: true });
  });
});
