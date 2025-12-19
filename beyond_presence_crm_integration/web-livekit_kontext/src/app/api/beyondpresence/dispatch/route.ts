import { NextRequest, NextResponse } from 'next/server';
import { AgentDispatchClient } from 'livekit-server-sdk';
import { checkRateLimit, getClientIdentifier } from '@/lib/rateLimit';

/**
 * Dispatch an agent to an existing room
 * This endpoint is called when user clicks Voice/Video Agent button
 */
export async function POST(request: NextRequest) {
  // Rate limiting: 30 requests per minute per IP
  const clientId = getClientIdentifier(request);
  const rateLimitResult = checkRateLimit(clientId, { limit: 30, windowSeconds: 60 });
  
  if (!rateLimitResult.success) {
    return NextResponse.json(
      { error: 'Too many requests. Please try again later.' },
      { 
        status: 429,
        headers: {
          'X-RateLimit-Limit': rateLimitResult.limit.toString(),
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': rateLimitResult.resetTime.toString()
        }
      }
    );
  }

  try {
    const text = await request.text();
    if (!text) {
      return NextResponse.json(
        { error: 'Empty request body' },
        { status: 400 }
      );
    }

    const body = JSON.parse(text);
    const { roomName, agentName, livekitUrl } = body;

    if (!roomName || !agentName || !livekitUrl) {
      return NextResponse.json(
        { error: 'Missing required parameters: roomName, agentName, livekitUrl' },
        { status: 400 }
      );
    }

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;

    if (!apiKey || !apiSecret) {
      return NextResponse.json(
        { error: 'LiveKit API credentials not configured' },
        { status: 500 }
      );
    }

    const httpUrl = livekitUrl.replace('wss://', 'https://').replace('ws://', 'http://');
    const agentDispatchClient = new AgentDispatchClient(httpUrl, apiKey, apiSecret);

    console.log(`Dispatching ${agentName} to room ${roomName}...`);
    const dispatch = await agentDispatchClient.createDispatch(roomName, agentName);
    console.log('Agent dispatched:', dispatch);

    return NextResponse.json({
      success: true,
      dispatch: {
        agentName: agentName,
        roomName: roomName
      }
    });

  } catch (error: any) {
    console.error('Failed to dispatch agent:', error);
    return NextResponse.json(
      {
        error: error.message || 'Failed to dispatch agent',
        details: error.toString()
      },
      { status: 500 }
    );
  }
}
