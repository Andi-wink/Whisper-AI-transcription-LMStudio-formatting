import { NextRequest, NextResponse } from 'next/server';
import { AccessToken, RoomServiceClient, AgentDispatchClient } from 'livekit-server-sdk';
import { checkRateLimit, getClientIdentifier } from '@/lib/rateLimit';

/**
 * Generate a LiveKit token for a user to join a specific room
 */
async function generateLiveKitTokenForRoom(roomName: string): Promise<string | null> {
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;

  if (!apiKey || !apiSecret || apiSecret === 'REPLACE_WITH_YOUR_SECRET') {
    return null;
  }

  const viewerIdentity = `identity-${Math.random().toString(36).substring(7)}`;

  const token = new AccessToken(apiKey, apiSecret, {
    identity: viewerIdentity,
    name: 'User',
    ttl: '24h',
  });

  // User needs full permissions for voice interaction
  token.addGrant({
    room: roomName,
    roomJoin: true,
    canSubscribe: true,
    canPublish: true,
    canPublishData: true,
  });

  console.log(`Generated token for room: ${roomName}, identity: ${viewerIdentity}`);
  return await token.toJwt();
}

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
    // Handle empty body
    const text = await request.text();
    if (!text) {
      return NextResponse.json(
        { error: 'Empty request body' },
        { status: 400 }
      );
    }

    const body = JSON.parse(text);
    let { avatarId, livekitToken, livekitUrl, mode, preload } = body;

    if (!avatarId || !livekitUrl) {
      return NextResponse.json(
        { error: 'Missing required parameters' },
        { status: 400 }
      );
    }

    // Default mode to video if not specified
    mode = mode || 'video';
    // Default preload to false (agent greets immediately)
    preload = preload === true;

    // Use unique room names for both voice and video
    const roomId = crypto.randomUUID().slice(0, 8);
    const roomName = mode === 'voice' 
      ? `voice-room-${roomId}` 
      : `avatar-room-${roomId}`;

    // Determine which agent to dispatch
    const agentName = 'avatar-agent'; // Agent checks mode via room metadata

    // Generate viewer token for this specific room
    const viewerToken = await generateLiveKitTokenForRoom(roomName);

    if (!viewerToken) {
      return NextResponse.json(
        {
          error: 'Unable to generate LiveKit tokens',
          help: 'Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET in .env.local'
        },
        { status: 400 }
      );
    }
    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;

    if (apiKey && apiSecret && livekitUrl) {
      try {
        const httpUrl = livekitUrl.replace('wss://', 'https://').replace('ws://', 'http://');
        const roomService = new RoomServiceClient(httpUrl, apiKey, apiSecret);
        const agentDispatchClient = new AgentDispatchClient(httpUrl, apiKey, apiSecret);

        // Create room with metadata (includes preload flag for agent to check)
        const roomMetadata = { mode, preload };
        try {
          await roomService.createRoom({
            name: roomName,
            emptyTimeout: 60 * 10, // 10 minutes
            metadata: JSON.stringify(roomMetadata)
          });
          console.log(`Created room ${roomName} with metadata:`, roomMetadata);
        } catch (roomError) {
          console.log('Room might already exist, trying to update metadata...');
        }

        // Dispatch agent - agent will check room metadata for preload flag before greeting
        try {
          console.log(`Dispatching ${agentName} to room ${roomName} (preload=${preload})...`);
          const dispatch = await agentDispatchClient.createDispatch(roomName, agentName);
          console.log('Agent dispatched:', dispatch);
        } catch (dispatchError) {
          console.error('Failed to dispatch agent:', dispatchError);
        }

      } catch (e) {
        console.error('Failed to update room metadata or dispatch agent:', e);
      }
    }

    // Return session data with token for the frontend
    return NextResponse.json({
      id: `session-${Date.now()}`,
      avatarId: avatarId,
      livekitToken: viewerToken,
      livekitUrl: livekitUrl,
      status: 'active',
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      debug: {
        roomName: roomName,
        mode: mode,
        agentName: agentName,
        preload: preload
      }
    });

  } catch (error: any) {
    console.error('Failed to create session:', error);
    return NextResponse.json(
      {
        error: error.message || 'Failed to create session',
        details: error.toString(),
        status: 500
      },
      { status: 500 }
    );
  }
}
