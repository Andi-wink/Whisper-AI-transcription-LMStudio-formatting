import logging
import os
import json
import asyncio
import aiohttp
from datetime import datetime

from dotenv import load_dotenv

from livekit import api
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import silero, openai, cartesia, deepgram
from livekit.plugins import bey
from livekit.agents.voice import AgentSession

from tools.insurance import InsuranceAssistant
from tools.hubspot_client import HubSpotClient

load_dotenv(".env.local")

# N8N Webhook for call summaries
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

logger = logging.getLogger("insurance-support-agent")
logger.setLevel(logging.INFO)

# Enable debug logging for livekit.agents
logging.getLogger("livekit.agents").setLevel(logging.DEBUG)

# Add file handler
fh = logging.FileHandler('agent_debug.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


# Initialize HubSpot client globally
hubspot_client = None
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
if HUBSPOT_ACCESS_TOKEN:
    hubspot_client = HubSpotClient(HUBSPOT_ACCESS_TOKEN)
    logger.info("HubSpot client initialized")
else:
    logger.warning("HUBSPOT_ACCESS_TOKEN not set - CRM tools will be disabled")


def _get_env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return v if v is not None and v.strip() != "" else default


async def send_call_summary_to_n8n(room_name: str, contact_id: str, session):
    """Send call summary to n8n webhook when session ends using session's chat context."""
    if not N8N_WEBHOOK_URL:
        logger.warning("N8N_WEBHOOK_URL not configured - call summary not sent")
        return
    
    # Extract transcript from session's chat context
    transcript_lines = []
    message_count = 0
    
    try:
        if session and hasattr(session, 'chat_ctx') and session.chat_ctx:
            for msg in session.chat_ctx.items:
                role = msg.role if hasattr(msg, 'role') else 'unknown'
                content = ''
                if hasattr(msg, 'text_content'):
                    content = msg.text_content
                elif hasattr(msg, 'content'):
                    content = str(msg.content) if msg.content else ''
                
                if content and role != 'system':  # Skip system prompts
                    transcript_lines.append(f"{role}: {content}")
                    message_count += 1
    except Exception as e:
        logger.error(f"Error extracting chat context: {e}")
    
    transcript = "\n".join(transcript_lines) if transcript_lines else "No conversation recorded"
    
    payload = {
        "event": "call.ended",
        "timestamp": datetime.now().isoformat(),
        "room_name": room_name,
        "contact_id": contact_id,
        "transcript": transcript,
        "message_count": message_count,
        "agent_name": "U-insure Support Agent"
    }

    logger.info(f"SESSION END: Sending call summary to n8n webhook")
    logger.info(f"Call summary payload: room={room_name}, messages={message_count}")
    logger.info(f"Transcript preview: {transcript[:200]}..." if len(transcript) > 200 else f"Transcript: {transcript}")

    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(N8N_WEBHOOK_URL, json=payload, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"SUCCESS: Call summary sent to n8n webhook")
                else:
                    logger.error(f"FAILED: n8n webhook returned status {response.status}")
    except Exception as e:
        logger.error(f"FAILED: Error sending call summary to n8n: {e}")


async def entrypoint(ctx: JobContext):
    """LiveKit agent that acts as an Insurance Support Agent with a Beyond Presence avatar."""

    # --- Room connect ---
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info(f"Agent connected to room: {ctx.room.name}")

    # Track conversation history for call summary
    conversation_history = []
    
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        logger.info(f"DEBUG: Track subscribed: {track.kind} from {participant.identity}")
    
    # Store session reference for disconnect handler (use list to allow mutation in closure)
    session_holder = [None]
    
    def trigger_call_summary(participant_identity):
        """Trigger call summary when user disconnects."""
        if session_holder[0]:
            logger.info(f"SESSION END: User {participant_identity} disconnected - sending call summary")
            asyncio.create_task(send_call_summary_to_n8n(ctx.room.name, contact_id, session_holder[0]))
        else:
            logger.warning("No session available for call summary")
    
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant):
        # Only trigger summary when a real user (not agent/avatar) disconnects
        if participant.identity.startswith("identity-"):
            trigger_call_summary(participant.identity)

    # Debug Env Vars
    logger.info(f"GROQ_API_KEY present: {bool(os.getenv('GROQ_API_KEY'))}")
    logger.info(f"ELEVENLABS_API_KEY present: {bool(os.getenv('ELEVENLABS_API_KEY'))}")
    logger.info(f"Elevenlabs_API_KEY present: {bool(os.getenv('Elevenlabs_API_KEY'))}")

    # --- Config ---
    # Avatar
    avatar_id = _get_env("BEY_AVATAR_ID", "7c9ca52f-d4f7-46e1-a4b8-0c8655857cc3")

    # Identify contact for CRM tools (in production, use caller ID or verification)
    test_email = os.getenv("TEST_CONTACT_EMAIL", "hs@cognifai.me")
    contact_id = None
    if hubspot_client:
        contact = await hubspot_client.get_contact_by_email(test_email)
        if contact:
            contact_id = contact["id"]
            logger.info(f"Identified contact: {contact.get('properties', {}).get('firstname')} (ID: {contact_id})")

    # Create InsuranceAssistant with HubSpot integration (tools defined in tools/insurance.py)
    agent = InsuranceAssistant(hubspot_client=hubspot_client, contact_id=contact_id)

    try:
        # Configure VAD - Tuning for better sensitivity
        vad = silero.VAD.load(
            min_speech_duration=0.1, # Lowered from default
            min_silence_duration=0.5,
            activation_threshold=0.4, # Lower threshold to trigger more easily
        )
        logger.info("VAD loaded with custom sensitivity")
        
        # Configure OpenAI LLM (better function calling support)
        llm = openai.LLM(
            model="gpt-4o-mini",
        )
        logger.info("OpenAI LLM initialized")

        # Configure STT via Deepgram (Nova-3)
        stt = deepgram.STT(
            model="nova-3",
            language="en-US",
        )
        logger.info("Deepgram STT initialized")

        # Configure TTS via Cartesia Sonic 3 (fast, high quality)
        tts = cartesia.TTS(
            model="sonic-2024-10-19",
            voice=os.getenv("CARTESIA_VOICE_ID", "3c7dfd17-3fa8-47aa-aacc-6313fe025442"),
            api_key=os.getenv("CARTESIA_API_KEY"),
        )
        logger.info("Cartesia Sonic TTS initialized")

        session = AgentSession(
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
        )
        session_holder[0] = session  # Store reference for disconnect handler
        logger.info("AgentSession created")
        
        @session.on("user_speech_started")
        def on_speech_started():
            logger.info("DEBUG: User speech started (VAD triggered)")

        @session.on("user_speech_committed")
        def on_speech_committed(msg):
            logger.info(f"DEBUG: User speech committed (STT Result): {msg.content}")
            conversation_history.append({"role": "user", "content": msg.content})

        @session.on("agent_speech_committed")
        def on_agent_speech_committed(msg):
            logger.info(f"DEBUG: Agent speech committed (LLM Result): {msg.content}")
            conversation_history.append({"role": "agent", "content": msg.content})

    except Exception as e:
        logger.error(f"Failed to initialize agent components: {e}", exc_info=True)
        return

    # --- Check Mode from Room Metadata ---
    mode = "video" # Default
    if ctx.room.metadata:
        try:
            metadata = json.loads(ctx.room.metadata)
            mode = metadata.get("mode", "video")
            logger.info(f"Room metadata parsed: {metadata}, mode: {mode}")
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse room metadata: {ctx.room.metadata}")
    
    logger.info(f"Agent running in {mode} mode")

    try:
        # --- Start agent session first (runs in background, enables say()) ---
        await session.start(room=ctx.room, agent=agent)
        logger.info("Agent session started.")

        # --- Beyond Presence avatar join (Only in video mode) ---
        if mode == "video":
            try:
                avatar = bey.AvatarSession(
                    avatar_id=avatar_id,
                    avatar_participant_identity="support-agent",
                    avatar_participant_name="U-insure Support",
                )

                logger.info("Starting avatar session…")
                await avatar.start(session, room=ctx.room)
                logger.info("Avatar joined the room.")
                
                # Brief delay to ensure avatar video is rendered on frontend
                await asyncio.sleep(1.5)
                    
            except Exception as e:
                logger.warning(f"Failed to connect to Beyond Presence avatar: {e}. Running in audio-only mode.")
        else:
            logger.info("Skipping avatar session (Voice Mode)")

        # --- Greeting - fires after avatar is ready ---
        await session.say("Hello, thank you for calling U-insure. My name is Nelly. How can I assist you with your policy today?")
        logger.info("Insurance Support Agent initialized and greeted successfully.")
        
        # --- Keep agent running until room closes ---
        # Wait for the room to be disconnected before exiting
        disconnect_event = asyncio.Event()
        
        @ctx.room.on("disconnected")
        def on_room_disconnected():
            logger.info("Room disconnected - agent shutting down")
            disconnect_event.set()
        
        await disconnect_event.wait()
        logger.info("Agent entrypoint exiting gracefully")
        
    except Exception as e:
        logger.error(f"Runtime error in agent loop: {e}", exc_info=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="avatar-agent",  # Only respond to explicit dispatches from frontend
    ))