"""
Generate a shareable playground link for testing the cloud agent.
Run: python generate_playground_link.py
"""
import os
import uuid
from livekit import api
from dotenv import load_dotenv

load_dotenv()

# Cloud credentials - update these with your LiveKit Cloud project credentials
CLOUD_URL = os.getenv("LIVEKIT_URL") or "wss://support-agent-me7v9squ.livekit.cloud"
CLOUD_API_KEY = os.getenv("LIVEKIT_API_KEY")
CLOUD_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

def generate_playground_url(tester_name: str = "Tester"):
    """Generate a shareable playground link for someone to test your agent."""
    
    if not all([CLOUD_URL, CLOUD_API_KEY, CLOUD_API_SECRET]):
        print("Error: Missing credentials!")
        print("Set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET in your .env file")
        print("Or update CLOUD_URL, CLOUD_API_KEY, CLOUD_API_SECRET in this script")
        return None

    # Generate unique room name for this test session
    room_name = f"playground-{uuid.uuid4().hex[:8]}"
    
    # Clean URL (remove wss:// prefix for the playground parameter)
    clean_url = CLOUD_URL.replace("wss://", "").replace("ws://", "")
    
    # Generate access token
    token = api.AccessToken(CLOUD_API_KEY, CLOUD_API_SECRET) \
        .with_identity(f"tester-{uuid.uuid4().hex[:6]}") \
        .with_name(tester_name) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )) \
        .to_jwt()

    # Construct playground URL
    playground_url = f"https://agents-playground.livekit.io/?tab=connect&url=wss://{clean_url}&token={token}"

    print("\n" + "="*60)
    print("🎮 SHAREABLE PLAYGROUND LINK")
    print("="*60)
    print(f"\n👤 Tester: {tester_name}")
    print(f"🏠 Room: {room_name}")
    print(f"\n🔗 Share this link:\n")
    print(playground_url)
    print("\n" + "="*60)
    print("📋 Instructions for tester:")
    print("="*60)
    print("1. Open the link above in a browser")
    print("2. Allow microphone access when prompted")
    print("3. Click 'Connect' if not auto-connected")
    print("4. The AI agent will greet you and respond to voice!")
    print("="*60 + "\n")
    
    return playground_url

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Guest Tester"
    generate_playground_url(name)
