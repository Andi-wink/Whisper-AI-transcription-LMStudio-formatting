import { test, expect } from '@playwright/test';

/**
 * E2E Test: Login Flow
 * 
 * Tests the authentication system with valid and invalid credentials.
 */

test.describe('Login Flow', () => {
  
  test('should show login page on initial visit', async ({ page }) => {
    await page.goto('/');
    
    // Should see login form elements
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Screenshot
    await page.screenshot({ path: 'e2e/screenshots/login-page.png' });
  });

  test('should login successfully with demo credentials', async ({ page }) => {
    await page.goto('/');
    
    // Fill in demo credentials
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Should redirect to landing page with agent selection
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Voice Agent')).toBeVisible();
    await expect(page.locator('text=Video Agent')).toBeVisible();
    
    // Should show welcome message with user name
    await expect(page.locator('text=Welcome')).toBeVisible();
    
    console.log('✅ Login successful with demo credentials');
  });

  test('should login successfully with admin credentials', async ({ page }) => {
    await page.goto('/');
    
    // Fill in admin credentials
    await page.fill('input[type="email"]', 'admin@uinsure.com');
    await page.fill('input[type="password"]', 'admin123');
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Should redirect to landing page
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    
    console.log('✅ Login successful with admin credentials');
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/');
    
    // Fill in invalid credentials
    await page.fill('input[type="email"]', 'invalid@test.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Should show error message and stay on login page
    // Error will be "User not found" for unknown email
    await expect(page.locator('text=User not found')).toBeVisible({ timeout: 5000 });
    
    // Should still see login form
    await expect(page.locator('input[type="email"]')).toBeVisible();
    
    console.log('✅ Invalid credentials correctly rejected');
  });

  test('should logout successfully', async ({ page }) => {
    await page.goto('/');
    
    // Login first
    await page.fill('input[type="email"]', 'demo@uinsure.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    // Wait for landing page
    await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
    
    // Click logout button
    await page.click('text=Logout');
    
    // Should return to login page
    await expect(page.locator('input[type="email"]')).toBeVisible({ timeout: 5000 });
    
    console.log('✅ Logout successful');
  });
});
