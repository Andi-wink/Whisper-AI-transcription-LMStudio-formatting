"""
Main Voice Agent - Refactored & Modular
========================================
Clean, modular voice agent with Beyond Presence avatar support.

Usage:
    python agent_main.py dev     # Development mode with hot reload
    python agent_main.py start   # Production mode
"""

from dotenv import load_dotenv
from livekit import agents
import os
import logging
import asyncio

# Local imports - modular components
from core import create_session, start_avatar
from integrations.hubspot import HubSpotClient
from agents.support_agent import SupportAgent

# Load environment variables
load_dotenv(".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("voice-agent")


async def entrypoint(ctx: agents.JobContext):
    """
    Main entry point for the voice agent.
    
    Flow:
    1. Connect to room
    2. Start CRM lookup (background)
    3. Create voice pipeline
    4. Start avatar (if configured)
    5. Start session with SupportAgent
    6. SupportAgent handles handoffs to ClaimsAgent via tools
    """
    
    # ============================================
    # 1. CONNECT TO ROOM
    # ============================================
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")

    # ============================================
    # 2. BACKGROUND CRM LOOKUP (non-blocking)
    # ============================================
    hubspot_client, hubspot_state = await _setup_hubspot()

    # ============================================
    # 3. CREATE VOICE PIPELINE
    # ============================================
    session = create_session()

    # ============================================
    # 4. START AVATAR (optional)
    # ============================================
    await start_avatar(session, ctx.room)

    # ============================================
    # 5. START SESSION WITH SUPPORT AGENT
    # ============================================
    # SupportAgent is the entry point - it handles handoffs to ClaimsAgent
    # ClaimsAgent is lazy-loaded only when user requests claim-related help
    agent = SupportAgent(
        hubspot_client=hubspot_client,
        hubspot_state=hubspot_state
    )
    
    await session.start(room=ctx.room, agent=agent)

    # ============================================
    # 6. INITIAL GREETING
    # ============================================
    await session.generate_reply(
        instructions="Greet the user professionally as an insurance support agent. "
                     "Keep it brief - just say hello and ask how you can help."
    )


async def _setup_hubspot() -> tuple:
    """
    Setup HubSpot client with background contact lookup.
    
    Returns:
        Tuple of (hubspot_client, hubspot_state)
    """
    hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    hubspot_client = HubSpotClient(hubspot_token) if hubspot_token else None
    hubspot_state = {"contact_id": None, "loaded": False}
    
    async def load_contact():
        if not hubspot_client:
            logger.warning("HUBSPOT_ACCESS_TOKEN not set. CRM features disabled.")
            return
        try:
            # TODO: Get email from caller ID or room metadata
            test_email = "hs@cognifai.me"
            contact = await hubspot_client.get_contact_by_email(test_email)
            if contact:
                hubspot_state["contact_id"] = contact["id"]
                logger.info(f"Loaded CRM contact: {test_email}")
        except Exception as e:
            logger.error(f"CRM lookup failed: {e}")
        finally:
            hubspot_state["loaded"] = True
    
    # Start lookup in background (non-blocking)
    asyncio.create_task(load_contact())
    
    return hubspot_client, hubspot_state


# ============================================
# ENTRYPOINT
# ============================================
if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )
