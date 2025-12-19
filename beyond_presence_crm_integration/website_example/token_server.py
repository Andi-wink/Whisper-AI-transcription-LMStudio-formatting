"""
LiveKit Token Server
Generates access tokens for website clients to connect to LiveKit rooms
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
import os
import time
import random
import string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="LiveKit Token Server")

# Configure CORS - IMPORTANT: In production, specify your actual domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000", 
        "http://127.0.0.1:8000",
        "https://your-website.com",  # Replace with your domain
        "*"  # Remove this in production!
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LiveKit configuration
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

# Validate configuration
if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL]):
    raise ValueError("Missing required environment variables: LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL")


def generate_room_name() -> str:
    """Generate unique room name"""
    timestamp = int(time.time())
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"demo-{timestamp}-{random_suffix}"


def generate_participant_name() -> str:
    """Generate unique participant identity"""
    random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"user-{random_id}"


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "LiveKit Token Server",
        "livekit_url": LIVEKIT_URL
    }


@app.get("/api/get-token")
async def get_token():
    """
    Generate LiveKit access token for a new room
    
    Returns:
        dict: Contains JWT token and LiveKit URL
    """
    try:
        # Generate unique identifiers
        room_name = generate_room_name()
        participant_name = generate_participant_name()
        
        # Create access token
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(participant_name)
        token.with_name(f"Guest {participant_name[-4:]}")  # Friendly display name
        
        # Grant permissions
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ))
        
        # Set token expiration (1 hour)
        token.with_ttl(3600)
        
        jwt_token = token.to_jwt()
        
        return {
            "token": jwt_token,
            "url": LIVEKIT_URL,
            "room_name": room_name,
            "participant_identity": participant_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")


@app.get("/api/get-token/{room_name}")
async def get_token_for_room(room_name: str):
    """
    Generate LiveKit access token for a specific room
    
    Args:
        room_name: Name of the room to join
        
    Returns:
        dict: Contains JWT token and LiveKit URL
    """
    try:
        participant_name = generate_participant_name()
        
        # Create access token
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(participant_name)
        token.with_name(f"Guest {participant_name[-4:]}")
        
        # Grant permissions
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ))
        
        token.with_ttl(3600)
        jwt_token = token.to_jwt()
        
        return {
            "token": jwt_token,
            "url": LIVEKIT_URL,
            "room_name": room_name,
            "participant_identity": participant_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "livekit_configured": bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET),
        "livekit_url": LIVEKIT_URL,
        "timestamp": int(time.time())
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("LiveKit Token Server")
    print("=" * 60)
    print(f"LiveKit URL: {LIVEKIT_URL}")
    print(f"API Key configured: {bool(LIVEKIT_API_KEY)}")
    print("=" * 60)
    print("\nStarting server on http://0.0.0.0:3000")
    print("Token endpoint: http://localhost:3000/api/get-token")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )
