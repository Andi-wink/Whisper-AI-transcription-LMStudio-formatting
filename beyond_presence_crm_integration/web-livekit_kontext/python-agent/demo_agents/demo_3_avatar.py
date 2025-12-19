"""
Demo 3: Beyond Presence Avatar Agent
====================================
- Visual avatar representation
- Same tools as basic agent

Run: python demo_agents/demo_3_avatar.py start

Requires: BEY_API_KEY, BEYOND_PRESENCE_AVATAR_ID
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentSession
from livekit.plugins import deepgram, openai, cartesia, bey
import os
import logging
import asyncio
import json

from config import PRELOADED_VAD
from integrations.hubspot import HubSpotClient
from integrations.call_summary import CallSummaryCollector, setup_call_summary
from agents.support_agent import SupportAgent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("demo-avatar")


async def entrypoint(ctx: agents.JobContext):
    """Insurance agent with Beyond Presence avatar."""
    
    # Must connect first for avatar to join
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")
    
    # Note: num_idle_processes=1 in WorkerOptions prevents duplicate agents
    # No need for additional duplicate detection here
    
    # Call summary collector
    call_summary = CallSummaryCollector(
        call_id=ctx.room.name,
        user_name="Andrew Winkler",
        user_email="andrew@automationmatters.org"
    )
    
    # HubSpot setup
    hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    hubspot_client = HubSpotClient(hubspot_token) if hubspot_token else None
    hubspot_state = {"contact_id": None, "loaded": False}
    
    async def load_hubspot_contact():
        if hubspot_client:
            try:
                contact = await hubspot_client.get_contact_by_email("hs@cognifai.me")
                if contact:
                    hubspot_state["contact_id"] = contact["id"]
                    logger.info(f"HubSpot contact: {hubspot_state['contact_id']}")
            except Exception as e:
                logger.error(f"HubSpot error: {e}")
        hubspot_state["loaded"] = True
    
    asyncio.create_task(load_hubspot_contact())

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", interim_results=True),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(model="sonic-turbo", voice="71a7ad14-091c-4e8e-a314-022ece01c121"),
        vad=PRELOADED_VAD,
    )

    # Beyond Presence Avatar - keep reference to prevent garbage collection
    avatar_session = None
    avatar_id = os.getenv("BEYOND_PRESENCE_AVATAR_ID") or os.getenv("BEY_AVATAR_ID")
    bey_api_key = os.getenv("BEY_API_KEY")
    
    # Fix LiveKit URL scheme if needed (Cloud injects https:// but bey needs wss://)
    livekit_url = os.getenv("LIVEKIT_URL", "")
    if livekit_url.startswith("https://"):
        fixed_url = livekit_url.replace("https://", "wss://")
        os.environ["LIVEKIT_URL"] = fixed_url
        logger.info(f"Fixed LIVEKIT_URL from https:// to wss://: {fixed_url}")
    
    logger.info(f"Avatar config - ID: {avatar_id}, API Key present: {bool(bey_api_key)}, URL: {os.getenv('LIVEKIT_URL')}")
    
    if avatar_id and bey_api_key:
        logger.info(f"Starting Beyond Presence avatar: {avatar_id}")
        try:
            avatar_session = bey.AvatarSession(
                avatar_id=avatar_id,
                avatar_participant_identity="support-agent",
                avatar_participant_name="U-insure Support",
            )
            logger.info("Avatar session created, starting...")
            await avatar_session.start(session, room=ctx.room)
            logger.info("Avatar started successfully!")
        except Exception as e:
            logger.error(f"Avatar failed with error: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Avatar traceback: {traceback.format_exc()}")
    elif not avatar_id:
        logger.warning("No BEYOND_PRESENCE_AVATAR_ID set. Running without avatar.")
    elif not bey_api_key:
        logger.warning("No BEY_API_KEY set. Running without avatar.")

    agent = SupportAgent(hubspot_client=hubspot_client, hubspot_state=hubspot_state)
    
    await session.start(room=ctx.room, agent=agent)
    
    # Set up call summary AFTER session starts to avoid interfering with avatar
    setup_call_summary(session, ctx.room, call_summary)
    
    # OPTION B: Check ROOM metadata for preload flag
    # If preload=true, wait for room metadata to change to preload=false before greeting
    greeted = False
    
    def parse_room_metadata():
        """Parse room metadata JSON, return dict or empty dict on error."""
        try:
            return json.loads(ctx.room.metadata or '{}')
        except:
            return {}
    
    async def send_greeting():
        """Send the greeting message."""
        nonlocal greeted
        if greeted:
            return
        greeted = True
        logger.info("Sending greeting to user!")
        await session.generate_reply(
            instructions="Greet the user by saying: 'Hello Andrew! Great to see you. I'm your U-insure assistant. What can I help you with today?' Be warm and smile."
        )
    
    # Check initial room metadata
    room_meta = parse_room_metadata()
    is_preload = room_meta.get('preload', False)
    logger.info(f"Room metadata: {room_meta}, preload={is_preload}")
    
    if not is_preload:
        # Not preload mode - greet immediately
        logger.info("Not in preload mode - greeting immediately")
        await send_greeting()
    else:
        # Preload mode - wait for room metadata to change to preload=false
        logger.info("In preload mode - waiting for room metadata change...")
        
        @ctx.room.on("room_metadata_changed")
        def on_room_metadata_changed(old_metadata: str, new_metadata: str):
            logger.info(f"Room metadata changed: {old_metadata} -> {new_metadata}")
            try:
                new_meta = json.loads(new_metadata or '{}')
                if not new_meta.get('preload', False):
                    logger.info("Preload mode disabled - triggering greeting")
                    asyncio.create_task(send_greeting())
            except Exception as e:
                logger.error(f"Error parsing room metadata: {e}")


async def request_fnc(req: agents.JobRequest) -> agents.AutoSubscribe:
    """Accept jobs for avatar rooms and playground testing."""
    if req.room.name.startswith(("avatar-room-", "playground-")):
        logger.info(f"Accepting avatar job for room: {req.room.name}")
        await req.accept()
        return agents.AutoSubscribe.SUBSCRIBE_ALL
    else:
        logger.info(f"Rejecting job for room: {req.room.name}")
        await req.reject()
        return agents.AutoSubscribe.SUBSCRIBE_NONE


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_fnc,  # Filter to avatar and playground rooms
        agent_name="avatar-agent",  # Required to ensure cloud agent doesn't race
        num_idle_processes=1,
    ))
