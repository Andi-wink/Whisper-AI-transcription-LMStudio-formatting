"""
Demo 4: Multi-Agent with Claims Handoff
=======================================
- Support Agent handles general inquiries
- Transfers to Claims Agent for claim-specific requests
- Demonstrates agent-to-agent handoff

Run: python demo_agents/demo_4_handoff.py start
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import deepgram, groq, cartesia
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
logger = logging.getLogger("demo-handoff")


class ClaimsAgent(Agent):
    """Specialized Claims Agent for handling insurance claims."""

    def __init__(self, hubspot_client=None, hubspot_state: dict = None, return_to_support=None):
        super().__init__(
            instructions="""You are a specialized Claims Agent at Uinsure.
            
            You handle all claim-related inquiries:
            - Filing new claims
            - Checking claim status
            - Providing claim documentation requirements
            
            IMPORTANT:
            - Be thorough but efficient with claims.
            - Ask for incident details, date, and policy number.
            - ALWAYS confirm after completing an action.
            - If the user has non-claims questions, offer to transfer back to Support.
            - NEVER output function call syntax. Speak naturally.""",
            tts=cartesia.TTS(model="sonic-turbo", voice="a0e99841-438c-4a64-b679-ae501e7d6091"),  # Male voice
        )
        self.hubspot = hubspot_client
        self.hubspot_state = hubspot_state or {}
        self.return_to_support = return_to_support
        self.claims = []

    async def on_enter(self) -> None:
        """Called when this agent takes over - introduce ourselves."""
        await self.session.generate_reply(
            instructions="Introduce yourself as the Claims Specialist. Say: 'Hi Andrew, this is the Claims team speaking. I understand you need help with a claim. What happened and how can I assist you today?'"
        )

    @function_tool
    async def file_claim(
        self, 
        context: RunContext, 
        policy_id: Annotated[str, "The policy ID for the claim"],
        incident_date: Annotated[str, "Date of the incident (e.g., 'December 1, 2024')"],
        incident_description: Annotated[str, "Brief description of what happened"]
    ) -> str:
        """File a new insurance claim."""
        claim = {
            "claim_number": f"CLM{len(self.claims) + 2001}",
            "policy_id": policy_id,
            "date": incident_date,
            "description": incident_description,
            "status": "Submitted"
        }
        self.claims.append(claim)
        
        return f"Claim filed successfully! Your claim number is {claim['claim_number']}. An adjuster will contact you within 24-48 hours."

    @function_tool
    async def check_claim_status(
        self, 
        context: RunContext, 
        claim_number: Annotated[str, "The claim number to check (e.g., 'CLM2001')"]
    ) -> str:
        """Check the status of an existing claim."""
        for claim in self.claims:
            if claim["claim_number"] == claim_number:
                return f"Claim {claim_number}: Status is '{claim['status']}'. Filed on {claim['date']}."
        return f"Claim {claim_number} not found. Please verify the claim number."

    @function_tool
    async def transfer_to_support(
        self, 
        context: RunContext,
        reason: Annotated[str, "Reason for transfer"]
    ) -> Agent:
        """Transfer back to the Support Agent for non-claims inquiries."""
        logger.info(f"Transferring back to Support Agent: {reason}")
        if self.return_to_support:
            return self.return_to_support
        return self


class SupportAgentWithHandoff(Agent):
    """Support Agent that can hand off to Claims Agent."""

    def __init__(self, hubspot_client=None, hubspot_state: dict = None):
        super().__init__(
            instructions="""You are a helpful Insurance Support Agent at Uinsure.
            You handle general inquiries:
            - Policy information
            - Address updates
            - Registration plate updates
            - General questions
            
            IMPORTANT:
            - If the user wants to file a claim or has claim questions, FIRST say "Let me connect you with our Claims Specialist who can help you with that" THEN transfer to Claims.
            - ALWAYS announce the transfer before calling transfer_to_claims.
            - Keep responses concise and professional.
            - ALWAYS confirm back after completing an action (e.g., "I've updated your address to...")
            - NEVER output function call syntax. Speak naturally."""
        )
        self.hubspot = hubspot_client
        self.hubspot_state = hubspot_state or {}
        self._claims_agent = None

    def _get_contact_id(self) -> str | None:
        return self.hubspot_state.get('contact_id')

    @function_tool
    async def get_policy_info(
        self, 
        context: RunContext
    ) -> str:
        """Get policy information from CRM."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "I cannot access your account information right now."

        props = await self.hubspot.get_contact_policy_info(contact_id)
        if props:
            policy_info = props.get("policy_info", "")
            name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
            if policy_info:
                return f"Policy info for {name}: {policy_info}"
            return f"Account found ({name}), but no policy data on file."
        return "Could not retrieve policy information."

    @function_tool
    async def update_address(
        self, 
        context: RunContext, 
        city: Annotated[str, "City name"], 
        country: Annotated[str, "Country"], 
        postal_code: Annotated[str, "Postal/ZIP code"], 
        street_address: Annotated[str, "Street address"]
    ) -> str:
        """Update customer address in CRM."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "Cannot update address right now."

        success = await self.hubspot.update_contact_address(contact_id, {
            "city": city, "country": country,
            "postalCode": postal_code, "streetAddress": street_address
        })
        return "Address updated successfully." if success else "Failed to update address."

    @function_tool
    async def update_registration_plate(
        self, 
        context: RunContext, 
        plate_number: Annotated[str, "The vehicle registration plate number (e.g., 'ABC 123', 'XY12 ABC')"],
        vehicle_make_model: Annotated[str, "The vehicle make and model (e.g., 'BMW 3 Series', 'Toyota Corolla')"]
    ) -> str:
        """Update the user's vehicle registration plate and insured vehicle. Always ask for both."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "Cannot update registration plate right now."

        success = await self.hubspot.update_registration_plate(contact_id, plate_number, vehicle_make_model)
        if success:
            return f"I've updated your registration plate to {plate_number} and insured vehicle to {vehicle_make_model}."
        return "Failed to update registration plate."

    @function_tool
    async def transfer_to_claims(
        self, 
        context: RunContext,
        reason: Annotated[str, "Reason for transfer (e.g., 'file a claim', 'claim status')"]
    ) -> Agent:
        """Transfer to the Claims Agent for claim-related requests."""
        logger.info(f"Transferring to Claims Agent: {reason}")
        if not self._claims_agent:
            self._claims_agent = ClaimsAgent(
                hubspot_client=self.hubspot,
                hubspot_state=self.hubspot_state,
                return_to_support=self
            )
        return self._claims_agent


async def entrypoint(ctx: agents.JobContext):
    """Multi-agent insurance system with handoff."""
    
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
                    logger.info(f"HubSpot contact: {hubspot_state['contact_id']}")
            except Exception as e:
                logger.error(f"HubSpot error: {e}")
        hubspot_state["loaded"] = True
    
    asyncio.create_task(load_hubspot_contact())

    session = AgentSession(
        stt=deepgram.STT(model="nova-2", interim_results=True),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=cartesia.TTS(model="sonic-turbo", voice="71a7ad14-091c-4e8e-a314-022ece01c121"),
        vad=PRELOADED_VAD,
    )

    agent = SupportAgentWithHandoff(hubspot_client=hubspot_client, hubspot_state=hubspot_state)
    
    # Set up call summary collection
    setup_call_summary(session, ctx.room, call_summary)
    
    await session.start(room=ctx.room, agent=agent)
    await session.generate_reply(
        instructions="Greet the user by saying: 'Hi Andrew, thanks for calling Uinsure! I'm here to help with your policy needs. And if you need assistance with any claims, I can connect you with our Claims Specialist.' Be friendly and professional."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        num_idle_processes=1,
    ))
