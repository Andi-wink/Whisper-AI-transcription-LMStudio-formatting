"""
Demo 1: Basic Insurance Agent
=============================
- Policy lookup
- Address updates
- Registration plate updates
- Support tickets

Run: python demo_agents/demo_1_basic.py start
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentSession
from livekit.plugins import groq, cartesia
import os
import logging
import asyncio

from config import PRELOADED_VAD
from integrations.hubspot import HubSpotClient
from integrations.call_summary import CallSummaryCollector, setup_call_summary
from agents.support_agent import SupportAgent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("demo-basic")


async def entrypoint(ctx: agents.JobContext):
    """Basic insurance support agent."""
    
    # Connect to room first
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")
    
    # Note: num_idle_processes=1 in WorkerOptions prevents duplicate agents
    # No need for additional duplicate detection here
    
    # Call summary collector - sends transcript to n8n at call end
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
        if not hubspot_client:
            return
        try:
            contact = await hubspot_client.get_contact_by_email("hs@cognifai.me")
            if contact:
                hubspot_state["contact_id"] = contact["id"]
                logger.info(f"HubSpot contact found: {hubspot_state['contact_id']}")
        except Exception as e:
            logger.error(f"HubSpot error: {e}")
        hubspot_state["loaded"] = True
    
    asyncio.create_task(load_hubspot_contact())

    # Multilingual setup: Groq Whisper auto-detects language
    session = AgentSession(
        stt=groq.STT(model="whisper-large-v3", detect_language=True),  # Auto-detects English/German
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=cartesia.TTS(model="sonic-turbo", voice="71a7ad14-091c-4e8e-a314-022ece01c121"),
        vad=PRELOADED_VAD,
    )

    agent = SupportAgent(hubspot_client=hubspot_client, hubspot_state=hubspot_state, room=ctx.room)
    
    # Set up call summary collection (transcript + sentiment at call end)
    setup_call_summary(session, ctx.room, call_summary)
    
    await session.start(room=ctx.room, agent=agent)
    await session.generate_reply(
        instructions="Greet the user by saying: 'Hi Andrew, welcome to U-insure! How can I assist you today?' Be warm and friendly."
    )


async def request_fnc(req: agents.JobRequest) -> agents.AutoSubscribe:
    """Accept jobs for avatar, voice rooms and playground testing."""
    # Accept avatar rooms, voice rooms and playground rooms for testing
    if req.room.name.startswith(("avatar-room-", "voice-room-", "playground-")):
        logger.info(f"Accepting job for room: {req.room.name}")
        await req.accept()
        return agents.AutoSubscribe.SUBSCRIBE_ALL
    else:
        logger.info(f"Rejecting job for room: {req.room.name}")
        await req.reject()
        return agents.AutoSubscribe.SUBSCRIBE_NONE


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_fnc,  # Filter to voice and playground rooms
        # agent_name removed to enable automatic dispatch
        num_idle_processes=1,
    ))
