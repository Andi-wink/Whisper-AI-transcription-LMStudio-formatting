"""
Quick token generator for testing
Run this to get a room token for the web interface
"""

import os
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv()

def generate_token(room_name="test-room", participant_name="user1", valid_hours=24):
    """Generate a LiveKit room token"""
    
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ Error: LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in .env file")
        return None
    
    token = api.AccessToken(api_key, api_secret)
    token.with_identity(participant_name)
    token.with_name(participant_name)
    token.with_grants(
        api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        )
    )
    
    # Set expiration
    from datetime import datetime, timedelta
    token.with_ttl(timedelta(hours=valid_hours))
    
    jwt_token = token.to_jwt()
    
    print("\n" + "="*60)
    print("🎟️  LiveKit Room Token Generated!")
    print("="*60)
    print(f"\n📋 Room Name: {room_name}")
    print(f"👤 Participant: {participant_name}")
    print(f"⏰ Valid for: {valid_hours} hours")
    print(f"\n🔑 Token:\n{jwt_token}\n")
    print("="*60)
    print("\n💡 Copy this token and paste it into the web interface")
    print("   along with your LiveKit WebSocket URL\n")
    
    return jwt_token


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate LiveKit room token')
    parser.add_argument('--room', default='test-room', help='Room name (default: test-room)')
    parser.add_argument('--user', default='user1', help='User identity (default: user1)')
    parser.add_argument('--hours', type=int, default=24, help='Token validity in hours (default: 24)')
    
    args = parser.parse_args()
    
    generate_token(args.room, args.user, args.hours)
