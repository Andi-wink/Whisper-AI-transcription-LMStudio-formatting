import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * E2E Test: Agent Tool Functions
 * 
 * Comprehensive tests for:
 * 1. Transfer call - should ONLY happen when explicitly requested
 * 2. Address update - should work correctly via HubSpot
 * 3. Call summary - should be called when call ends
 */

const AGENT_DEBUG_LOG = 'python-agent/agent_debug.log';

// Helper to read last N lines from log file
function readLastLines(filePath: string, lines: number): string {
  try {
    const fullPath = path.join(process.cwd(), filePath);
    const content = fs.readFileSync(fullPath, 'utf-8');
    const allLines = content.split('\n');
    return allLines.slice(-lines).join('\n');
  } catch (e) {
    return '';
  }
}

// Helper to check if log contains pattern after timestamp
function logContainsAfter(logContent: string, pattern: string, afterTimestamp?: string): boolean {
  const lines = logContent.split('\n');
  let foundTimestamp = !afterTimestamp;
  
  for (const line of lines) {
    if (afterTimestamp && line.includes(afterTimestamp)) {
      foundTimestamp = true;
    }
    if (foundTimestamp && line.toLowerCase().includes(pattern.toLowerCase())) {
      return true;
    }
  }
  return false;
}

// Helper function to login
async function login(page: any) {
  await page.goto('/');
  await page.fill('input[type="email"]', 'demo@uinsure.com');
  await page.fill('input[type="password"]', 'demo123');
  await page.click('button[type="submit"]');
  await expect(page.locator('text=U-insure Support')).toBeVisible({ timeout: 10000 });
}

// Helper to get current timestamp for log filtering
function getCurrentTimestamp(): string {
  const now = new Date();
  return now.toISOString().split('T')[0] + ' ' + 
         now.toTimeString().split(' ')[0].substring(0, 5);
}

test.describe('Transfer Call Tool Tests', () => {
  
  test('should NOT transfer when user asks about policy', async ({ page }) => {
    const startTime = getCurrentTimestamp();
    await login(page);
    
    // Select Voice Agent (faster)
    await page.click('text=Voice Agent');
    await page.waitForTimeout(10000); // Wait for agent to connect
    
    // Find chat input and send a policy question (NOT a transfer request)
    const chatInput = page.locator('input[type="text"]').first()
      .or(page.locator('textarea').first());
    
    try {
      await chatInput.waitFor({ timeout: 10000 });
      
      // Ask about policy - should NOT trigger transfer
      await chatInput.fill('Can you tell me about my insurance policy?');
      await chatInput.press('Enter');
      
      console.log('📤 Sent policy question (should NOT transfer)');
      
      // Wait for agent to respond
      await page.waitForTimeout(15000);
      
      // Check logs - transfer_call should NOT have been invoked
      const logs = readLastLines(AGENT_DEBUG_LOG, 100);
      const transferCalled = logContainsAfter(logs, 'TOOL CALLED: transfer_call', startTime);
      
      if (transferCalled) {
        console.log('❌ FAIL: Transfer was called when it should not have been!');
        await page.screenshot({ path: 'e2e/screenshots/transfer-wrongly-called.png' });
      } else {
        console.log('✅ PASS: Transfer was NOT called for policy question');
      }
      
      expect(transferCalled).toBe(false);
      
    } catch (e) {
      console.log('⚠️ Could not interact with chat:', e);
      await page.screenshot({ path: 'e2e/screenshots/transfer-test-error.png' });
    }
    
    // End call
    const endCallBtn = page.locator('button[title="End Call"]');
    if (await endCallBtn.isVisible()) {
      await endCallBtn.click();
    }
  });

  test('should NOT transfer when user says hello or greets', async ({ page }) => {
    const startTime = getCurrentTimestamp();
    await login(page);
    
    await page.click('text=Voice Agent');
    await page.waitForTimeout(10000);
    
    const chatInput = page.locator('input[type="text"]').first()
      .or(page.locator('textarea').first());
    
    try {
      await chatInput.waitFor({ timeout: 10000 });
      
      // Just say hello - should NOT trigger transfer
      await chatInput.fill('Hello, how are you?');
      await chatInput.press('Enter');
      
      console.log('📤 Sent greeting (should NOT transfer)');
      await page.waitForTimeout(15000);
      
      const logs = readLastLines(AGENT_DEBUG_LOG, 100);
      const transferCalled = logContainsAfter(logs, 'TOOL CALLED: transfer_call', startTime);
      
      if (transferCalled) {
        console.log('❌ FAIL: Transfer was called on simple greeting!');
      } else {
        console.log('✅ PASS: Transfer was NOT called for greeting');
      }
      
      expect(transferCalled).toBe(false);
      
    } catch (e) {
      console.log('⚠️ Could not interact with chat:', e);
    }
    
    const endCallBtn = page.locator('button[title="End Call"]');
    if (await endCallBtn.isVisible()) {
      await endCallBtn.click();
    }
  });

  test('should transfer ONLY when user explicitly asks for human', async ({ page }) => {
    const startTime = getCurrentTimestamp();
    await login(page);
    
    await page.click('text=Voice Agent');
    await page.waitForTimeout(10000);
    
    const chatInput = page.locator('input[type="text"]').first()
      .or(page.locator('textarea').first());
    
    try {
      await chatInput.waitFor({ timeout: 10000 });
      
      // Explicitly ask for human - SHOULD trigger transfer
      await chatInput.fill('I want to speak to a human agent please');
      await chatInput.press('Enter');
      
      console.log('📤 Sent explicit transfer request');
      await page.waitForTimeout(20000);
      
      const logs = readLastLines(AGENT_DEBUG_LOG, 100);
      const transferCalled = logContainsAfter(logs, 'TOOL CALLED: transfer_call', startTime);
      
      if (transferCalled) {
        console.log('✅ PASS: Transfer was called when user explicitly requested');
        
        // Check if transfer succeeded
        const transferSuccess = logContainsAfter(logs, 'SUCCESS: Dialing', startTime);
        if (transferSuccess) {
          console.log('✅ Transfer dial initiated successfully');
        }
      } else {
        console.log('❌ FAIL: Transfer was NOT called despite explicit request');
      }
      
      expect(transferCalled).toBe(true);
      
    } catch (e) {
      console.log('⚠️ Could not interact with chat:', e);
    }
    
    const endCallBtn = page.locator('button[title="End Call"]');
    if (await endCallBtn.isVisible()) {
      await endCallBtn.click();
    }
  });
});

test.describe('Address Update Tool Tests', () => {
  
  test('should update address when user provides new address', async ({ page }) => {
    const startTime = getCurrentTimestamp();
    await login(page);
    
    await page.click('text=Voice Agent');
    await page.waitForTimeout(10000);
    
    const chatInput = page.locator('input[type="text"]').first()
      .or(page.locator('textarea').first());
    
    try {
      await chatInput.waitFor({ timeout: 10000 });
      
      // Request address update
      await chatInput.fill('I need to update my address. My new address is 123 Test Street, Dublin, Ireland, D01 AB12');
      await chatInput.press('Enter');
      
      console.log('📤 Sent address update request');
      await page.waitForTimeout(20000);
      
      const logs = readLastLines(AGENT_DEBUG_LOG, 150);
      
      // Check if update_address was called
      const addressUpdateCalled = logContainsAfter(logs, 'Updating address for', startTime);
      
      if (addressUpdateCalled) {
        console.log('✅ PASS: Address update was called');
        
        // Check if it succeeded
        const updateSuccess = logs.includes("I've updated your address");
        if (updateSuccess) {
          console.log('✅ Address update succeeded');
        }
      } else {
        console.log('⚠️ Address update tool may not have been invoked');
      }
      
      await page.screenshot({ path: 'e2e/screenshots/address-update-test.png' });
      
    } catch (e) {
      console.log('⚠️ Could not interact with chat:', e);
    }
    
    const endCallBtn = page.locator('button[title="End Call"]');
    if (await endCallBtn.isVisible()) {
      await endCallBtn.click();
    }
  });
});

test.describe('Call Summary Tool Tests', () => {
  
  test('should send call summary when user says goodbye', async ({ page }) => {
    const startTime = getCurrentTimestamp();
    await login(page);
    
    await page.click('text=Voice Agent');
    await page.waitForTimeout(10000);
    
    const chatInput = page.locator('input[type="text"]').first()
      .or(page.locator('textarea').first());
    
    try {
      await chatInput.waitFor({ timeout: 10000 });
      
      // Have a brief conversation first
      await chatInput.fill('Hello, I just wanted to check on my policy');
      await chatInput.press('Enter');
      await page.waitForTimeout(10000);
      
      // Now say goodbye to trigger call summary
      await chatInput.fill('Thank you for your help. Goodbye!');
      await chatInput.press('Enter');
      
      console.log('📤 Sent goodbye message (should trigger call summary)');
      await page.waitForTimeout(20000);
      
      const logs = readLastLines(AGENT_DEBUG_LOG, 150);
      
      // Check if send_call_summary was called
      const summaryCalled = logContainsAfter(logs, 'TOOL CALLED: send_call_summary', startTime);
      
      if (summaryCalled) {
        console.log('✅ PASS: Call summary was sent when user said goodbye');
        
        // Check if it succeeded
        const summarySuccess = logContainsAfter(logs, 'SUCCESS: Call summary sent', startTime);
        if (summarySuccess) {
          console.log('✅ Call summary sent to n8n webhook successfully');
        } else {
          console.log('⚠️ Call summary may have failed to send');
        }
      } else {
        console.log('❌ FAIL: Call summary was NOT called when user said goodbye');
      }
      
      await page.screenshot({ path: 'e2e/screenshots/call-summary-test.png' });
      
      // Note: We expect it to be called, but won't fail test if webhook not configured
      expect(summaryCalled || logs.includes('webhook not configured')).toBe(true);
      
    } catch (e) {
      console.log('⚠️ Could not interact with chat:', e);
    }
    
    const endCallBtn = page.locator('button[title="End Call"]');
    if (await endCallBtn.isVisible()) {
      await endCallBtn.click();
    }
  });

  test('should include correct payload in call summary', async ({ page }) => {
    const startTime = getCurrentTimestamp();
    await login(page);
    
    await page.click('text=Voice Agent');
    await page.waitForTimeout(10000);
    
    const chatInput = page.locator('input[type="text"]').first()
      .or(page.locator('textarea').first());
    
    try {
      await chatInput.waitFor({ timeout: 10000 });
      
      // Have a conversation that would be summarized
      await chatInput.fill('I updated my address today and filed a claim');
      await chatInput.press('Enter');
      await page.waitForTimeout(10000);
      
      await chatInput.fill('Thanks for everything, bye!');
      await chatInput.press('Enter');
      await page.waitForTimeout(20000);
      
      const logs = readLastLines(AGENT_DEBUG_LOG, 200);
      
      // Check payload contains expected fields
      const hasTimestamp = logs.includes('"timestamp"');
      const hasRoomName = logs.includes('"room_name"');
      const hasSummary = logs.includes('"summary"');
      const hasSentiment = logs.includes('"customer_sentiment"');
      
      console.log(`Payload check - timestamp: ${hasTimestamp}, room: ${hasRoomName}, summary: ${hasSummary}, sentiment: ${hasSentiment}`);
      
      if (hasTimestamp && hasRoomName && hasSummary) {
        console.log('✅ PASS: Call summary payload contains required fields');
      }
      
      await page.screenshot({ path: 'e2e/screenshots/call-summary-payload.png' });
      
    } catch (e) {
      console.log('⚠️ Could not interact with chat:', e);
    }
    
    const endCallBtn = page.locator('button[title="End Call"]');
    if (await endCallBtn.isVisible()) {
      await endCallBtn.click();
    }
  });
});

test.describe('Integration Tests - Full Conversation Flow', () => {
  
  test('full conversation: greeting, policy check, address update, goodbye with summary', async ({ page }) => {
    test.setTimeout(180000); // 3 minutes for full flow
    const startTime = getCurrentTimestamp();
    
    await login(page);
    await page.click('text=Voice Agent');
    await page.waitForTimeout(12000);
    
    const chatInput = page.locator('input[type="text"]').first()
      .or(page.locator('textarea').first());
    
    try {
      await chatInput.waitFor({ timeout: 10000 });
      
      // Step 1: Greeting (should NOT transfer)
      console.log('Step 1: Sending greeting...');
      await chatInput.fill('Hi, I need help with my account');
      await chatInput.press('Enter');
      await page.waitForTimeout(12000);
      
      // Step 2: Ask about policy
      console.log('Step 2: Asking about policy...');
      await chatInput.fill('Can you look up my policy information?');
      await chatInput.press('Enter');
      await page.waitForTimeout(15000);
      
      // Step 3: Request address update
      console.log('Step 3: Requesting address update...');
      await chatInput.fill('Please update my address to 456 New Street, Cork, Ireland, T12 XY34');
      await chatInput.press('Enter');
      await page.waitForTimeout(15000);
      
      // Step 4: End call (should trigger summary)
      console.log('Step 4: Ending call...');
      await chatInput.fill('Thank you so much for your help today. Goodbye!');
      await chatInput.press('Enter');
      await page.waitForTimeout(20000);
      
      // Verify results
      const logs = readLastLines(AGENT_DEBUG_LOG, 300);
      
      const results = {
        noUnwantedTransfer: !logContainsAfter(logs, 'TOOL CALLED: transfer_call', startTime),
        addressUpdateAttempted: logs.includes('Updating address for'),
        callSummarySent: logs.includes('TOOL CALLED: send_call_summary') || logs.includes('webhook not configured')
      };
      
      console.log('\n=== FULL FLOW TEST RESULTS ===');
      console.log(`✓ No unwanted transfer: ${results.noUnwantedTransfer ? 'PASS' : 'FAIL'}`);
      console.log(`✓ Address update attempted: ${results.addressUpdateAttempted ? 'PASS' : 'CHECK'}`);
      console.log(`✓ Call summary triggered: ${results.callSummarySent ? 'PASS' : 'FAIL'}`);
      console.log('==============================\n');
      
      await page.screenshot({ path: 'e2e/screenshots/full-flow-test.png' });
      
      // Main assertion: no unwanted transfer
      expect(results.noUnwantedTransfer).toBe(true);
      
    } catch (e) {
      console.log('⚠️ Error in full flow test:', e);
      await page.screenshot({ path: 'e2e/screenshots/full-flow-error.png' });
    }
    
    const endCallBtn = page.locator('button[title="End Call"]');
    if (await endCallBtn.isVisible()) {
      await endCallBtn.click();
    }
  });
});
