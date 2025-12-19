"""
Minimal LiveKit + Beyond Presence Interactive Avatar Test Agent
"""

import asyncio
import logging
import os
from typing import Annotated
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BeyondPresenceAvatar:
    """Handles Beyond Presence avatar integration"""
    
    def __init__(self, api_key: str, avatar_id: str):
        self.api_key = api_key
        self.avatar_id = avatar_id
        self.base_url = "https://api.beyondpresence.ai/v1"
        
    async def get_avatar_config(self):
        """Get avatar configuration from Beyond Presence"""
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/avatars/{self.avatar_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch avatar: {response.status}")
                    return None


class HubSpotManager(llm.FunctionContext):
    """
    Manager for HubSpot CRM interactions.
    Allows the agent to create and retrieve contacts.
    """
    def __init__(self, access_token: str):
        super().__init__()
        self.client = HubSpot(access_token=access_token)
        logger.info("HubSpotManager initialized")

    @llm.ai_callable(description="Create a new contact in HubSpot")
    def create_contact(
        self,
        email: Annotated[str, llm.TypeInfo(description="The email address of the contact")],
        firstname: Annotated[str, llm.TypeInfo(description="The first name of the contact")],
        lastname: Annotated[str, llm.TypeInfo(description="The last name of the contact")],
    ) -> str:
        """Create a contact in HubSpot"""
        try:
            properties = {
                "email": email,
                "firstname": firstname,
                "lastname": lastname
            }
            simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
                properties=properties
            )
            api_response = self.client.crm.contacts.basic_api.create(
                simple_public_object_input_for_create=simple_public_object_input_for_create
            )
            logger.info(f"Created contact: {api_response}")
            return f"Successfully created contact for {firstname} {lastname} with ID {api_response.id}"
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return f"Failed to create contact: {str(e)}"

    @llm.ai_callable(description="Get a contact by email from HubSpot")
    def get_contact(
        self,
        email: Annotated[str, llm.TypeInfo(description="The email address to search for")]
    ) -> str:
        """Get a contact by email"""
        try:
            # Note: This uses the search API which might require different scopes or higher tier.
            # For simplicity in this basic integration, we'll try to use the basic API if possible, 
            # but search is the standard way to find by email.
            # Alternatively, we can just say we can't find it if we don't want to implement search complexity.
            # Let's try a simple search.
            
            from hubspot.crm.contacts import PublicObjectSearchRequest, FilterGroup, Filter

            public_object_search_request = PublicObjectSearchRequest(
                filter_groups=[
                    FilterGroup(
                        filters=[
                            Filter(
                                property_name="email",
                                operator="EQ",
                                value=email
                            )
                        ]
                    )
                ]
            )
            api_response = self.client.crm.contacts.search_api.do_search(
                public_object_search_request=public_object_search_request
            )
            
            if api_response.results:
                contact = api_response.results[0]
                return f"Found contact: {contact.properties.get('firstname')} {contact.properties.get('lastname')} (ID: {contact.id})"
            else:
                return "No contact found with that email."
        except Exception as e:
            logger.error(f"Error searching contact: {e}")
            return f"Failed to find contact: {str(e)}"


async def entrypoint(ctx: JobContext):
    """Main agent entrypoint"""
    
    logger.info(f"Starting agent for room: {ctx.room.name}")
    
    # Initialize Beyond Presence avatar (optional for local testing)
    beyond_api_key = os.getenv("BEYOND_PRESENCE_API_KEY")
    avatar_id = os.getenv("BEYOND_PRESENCE_AVATAR_ID")
    
    if beyond_api_key and avatar_id:
        try:
            avatar = BeyondPresenceAvatar(beyond_api_key, avatar_id)
            # We just fetch it to verify it works, but in a real app we might pass config to the frontend
            avatar_config = await avatar.get_avatar_config()
            if avatar_config:
                logger.info(f"Avatar loaded: {avatar_config.get('name', 'Unknown')}")
        except Exception as e:
            logger.warning(f"Beyond Presence avatar unavailable (running without video avatar): {e}")
    else:
        logger.info("Beyond Presence credentials not set. Agent will run in audio-only mode.")
    
    # Initialize HubSpot
    hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    fnc_ctx = None
    if hubspot_token:
        fnc_ctx = HubSpotManager(hubspot_token)
    else:
        logger.warning("HUBSPOT_ACCESS_TOKEN not set. CRM features disabled.")

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    # Initialize voice assistant with OpenAI
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(
            model="gpt-4o-mini",
        ),
        tts=openai.TTS(
            voice="alloy",
        ),
        fnc_ctx=fnc_ctx,
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=(
                "You are a friendly AI assistant with an interactive avatar. "
                "You can help manage contacts in HubSpot CRM. "
                "Keep your responses concise and natural. "
                "You can see and hear the user through the avatar interface."
            ),
        ),
    )
    
    # Start the assistant
    assistant.start(ctx.room)
    
    # Send initial greeting
    await assistant.say("Hello! I'm your interactive AI avatar. How can I help you today?")
    
    logger.info("Voice assistant started successfully")


if __name__ == "__main__":
    # Run the agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL"),
        )
    )
