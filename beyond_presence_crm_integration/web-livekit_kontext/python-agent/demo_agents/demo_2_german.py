"""
Demo 2: German-Speaking Insurance Agent
=======================================
- Bilingual: German and English
- Same tools as basic agent

Run: python demo_agents/demo_2_german.py start
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import groq, elevenlabs
from typing import Annotated
from datetime import datetime
import os
import logging
import asyncio

from config import PRELOADED_VAD
from integrations.hubspot import HubSpotClient
from integrations.call_summary import CallSummaryCollector, setup_call_summary

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("demo-german")


class GermanSupportAgent(Agent):
    """Bilingual German/English Insurance Support Agent."""

    def __init__(self, hubspot_client=None, hubspot_state: dict = None):
        super().__init__(
            instructions="""Du bist ein freundlicher und professioneller Versicherungs-Kundenberater.
            You are also fluent in English and can switch languages based on user preference.
            
            Du kannst helfen mit:
            - Policen-Informationen abrufen (Get policy info)
            - Adresse aktualisieren (Update address)
            - Kfz-Kennzeichen aktualisieren (Update registration plate)
            - Support-Tickets erstellen (Create support tickets)
            
            WICHTIGE REGELN / IMPORTANT RULES:
            - Antworte in der Sprache, die der Benutzer verwendet.
            - Respond in the language the user speaks.
            - Halte Antworten kurz und professionell.
            - NIEMALS Funktions-Syntax aussprechen. Sprich natürlich.
            - NEVER output function call syntax. Speak naturally.
            - IMMER bestätigen nach einer Aktion: "Ich habe Ihre Adresse aktualisiert..." / "Ihr Kennzeichen wurde geändert..."
            - ALWAYS confirm after completing an action: "I've updated your address to..." / "Your plate has been changed to..."
            
            Wenn der Benutzer Deutsch spricht, antworte auf Deutsch.
            If the user speaks English, respond in English."""
        )
        self.hubspot = hubspot_client
        self.hubspot_state = hubspot_state or {}

    def _get_contact_id(self) -> str | None:
        return self.hubspot_state.get('contact_id')

    @function_tool
    async def get_policy_info(
        self, 
        context: RunContext
    ) -> str:
        """Policen-Informationen abrufen / Get policy information from CRM."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "Ich kann derzeit nicht auf Ihre Kontoinformationen zugreifen. / I cannot access your account right now."

        props = await self.hubspot.get_contact_policy_info(contact_id)
        if props:
            policy_info = props.get("policy_info", "")
            name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
            if policy_info:
                return f"Policen-Info für {name}: {policy_info}"
            return f"Konto gefunden ({name}), aber keine Policen-Daten hinterlegt."
        return "Policen-Informationen konnten nicht abgerufen werden."

    @function_tool
    async def update_address(
        self, 
        context: RunContext, 
        city: Annotated[str, "Stadt / City"], 
        country: Annotated[str, "Land / Country"], 
        postal_code: Annotated[str, "Postleitzahl / Postal code"], 
        street_address: Annotated[str, "Straße und Hausnummer / Street address"]
    ) -> str:
        """Adresse im CRM aktualisieren / Update address in CRM."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "Adresse kann derzeit nicht aktualisiert werden."

        success = await self.hubspot.update_contact_address(contact_id, {
            "city": city, "country": country,
            "postalCode": postal_code, "streetAddress": street_address
        })
        return "Adresse erfolgreich aktualisiert." if success else "Fehler beim Aktualisieren der Adresse."

    @function_tool
    async def update_registration_plate(
        self, 
        context: RunContext, 
        plate_number: Annotated[str, "Kfz-Kennzeichen / Vehicle registration plate"]
    ) -> str:
        """Kfz-Kennzeichen aktualisieren / Update vehicle registration plate."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "Kennzeichen kann derzeit nicht aktualisiert werden."

        success = await self.hubspot.update_registration_plate(contact_id, plate_number)
        return f"Kennzeichen auf {plate_number} aktualisiert." if success else "Fehler beim Aktualisieren."


async def entrypoint(ctx: agents.JobContext):
    """German-speaking insurance agent."""
    
    # Connect to room first
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")
    
    # Check if there's already an agent in the room (prevent duplicates)
    for participant in ctx.room.remote_participants.values():
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
            logger.warning(f"Agent already in room, exiting to prevent duplicate")
            return
    
    # Call summary collector
    call_summary = CallSummaryCollector(
        call_id=ctx.room.name,
        user_name="Andrew Winkler",
        user_email="andrew@automationmatters.org"
    )
    
    hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    hubspot_client = HubSpotClient(hubspot_token) if hubspot_token else None
    hubspot_state = {"contact_id": None, "loaded": False}
    
    async def load_hubspot_contact():
        if hubspot_client:
            try:
                contact = await hubspot_client.get_contact_by_email("hs@cognifai.me")
                if contact:
                    hubspot_state["contact_id"] = contact["id"]
            except Exception as e:
                logger.error(f"HubSpot error: {e}")
        hubspot_state["loaded"] = True
    
    asyncio.create_task(load_hubspot_contact())

    eleven_key = os.getenv("ELEVENLABS_API_KEY")
    # German voice - Nicole or use multilingual
    voice_id = os.getenv("ELEVENLABS_GERMAN_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    session = AgentSession(
        stt=groq.STT(
            model="whisper-large-v3",
            detect_language=True,  # Auto-detect German/English
        ),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=elevenlabs.TTS(api_key=eleven_key, voice_id=voice_id),
        vad=PRELOADED_VAD,
    )

    agent = GermanSupportAgent(hubspot_client=hubspot_client, hubspot_state=hubspot_state)
    
    # Set up call summary collection
    setup_call_summary(session, ctx.room, call_summary)
    
    await session.start(room=ctx.room, agent=agent)
    await session.generate_reply(
        instructions="Greet the user in German by saying: 'Hallo Andrew, willkommen bei Uinsure! Wie kann ich Ihnen heute behilflich sein?' Be warm and professional."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        num_idle_processes=1,
    ))
