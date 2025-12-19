import { NextRequest, NextResponse } from 'next/server';
import { AccessToken } from 'livekit-server-sdk';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const room = searchParams.get('room') || 'default-room';
    const identity = searchParams.get('identity') || 'user-' + Math.random().toString(36).substring(7);

    // Get LiveKit credentials from environment (server-side only, never exposed)
    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;

    if (!apiKey || !apiSecret) {
      console.error('LiveKit credentials missing - check LIVEKIT_API_KEY and LIVEKIT_API_SECRET');
      return NextResponse.json(
        { error: 'Server configuration error' },
        { status: 500 }
      );
    }

    // Create a new token
    const token = new AccessToken(apiKey, apiSecret, {
      identity: identity,
      ttl: '24h', // Token valid for 24 hours
    });

    // Grant permissions
    token.addGrant({
      room: room,
      roomJoin: true,
      canSubscribe: true,
      canPublish: true,
      canPublishData: true,
    });

    const jwt = await token.toJwt();

    return NextResponse.json({
      token: jwt,
      url: process.env.NEXT_PUBLIC_DEMO_LIVEKIT_URL || 'wss://cdtm-hack-msw7nj13.livekit.cloud',
      room: room,
      identity: identity
    });

  } catch (error: any) {
    console.error('Failed to generate LiveKit token:', error);
    
    return NextResponse.json(
      {
        error: error.message || 'Failed to generate token',
        details: error.toString()
      },
      { status: 500 }
    );
  }
}
