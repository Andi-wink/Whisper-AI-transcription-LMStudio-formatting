import { NextRequest, NextResponse } from 'next/server';
import { RoomServiceClient } from 'livekit-server-sdk';

/**
 * Update room metadata - used to signal agent when user is ready
 * POST /api/beyondpresence/room-metadata
 * Body: { roomName: string, metadata: object }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { roomName, metadata, livekitUrl } = body;

    if (!roomName || !metadata) {
      return NextResponse.json(
        { error: 'Missing required parameters: roomName, metadata' },
        { status: 400 }
      );
    }

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const url = livekitUrl || process.env.NEXT_PUBLIC_DEMO_LIVEKIT_URL;

    if (!apiKey || !apiSecret || !url) {
      return NextResponse.json(
        { error: 'LiveKit credentials not configured' },
        { status: 500 }
      );
    }

    const httpUrl = url.replace('wss://', 'https://').replace('ws://', 'http://');
    const roomService = new RoomServiceClient(httpUrl, apiKey, apiSecret);

    // Update room metadata
    const metadataString = JSON.stringify(metadata);
    await roomService.updateRoomMetadata(roomName, metadataString);

    console.log(`Updated room ${roomName} metadata to:`, metadata);

    return NextResponse.json({
      success: true,
      roomName,
      metadata
    });

  } catch (error: any) {
    console.error('Failed to update room metadata:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to update room metadata' },
      { status: 500 }
    );
  }
}
