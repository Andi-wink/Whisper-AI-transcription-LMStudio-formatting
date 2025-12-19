"""
Support Agent
=============
Voice agent for insurance support with HubSpot CRM integration.
Build: 2025-12-16-v2
"""

from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool
from livekit import api, rtc
from livekit.protocol.sip import TransferSIPParticipantRequest
from datetime import datetime
from typing import Annotated
import logging
import os
import re

logger = logging.getLogger("support-agent")


def sanitize_input(value: str, max_length: int = 200) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not value:
        return ""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';{}()\[\]\\]', '', str(value))
    # Trim to max length
    return sanitized[:max_length].strip()


class SupportAgent(Agent):
    """Insurance Support Agent with HubSpot CRM tools."""

    def __init__(self, hubspot_client=None, hubspot_state: dict = None, room: rtc.Room = None):
        super().__init__(
            instructions="""You are a helpful and professional Insurance Support Agent.
            You speak both English and German fluently - always respond in the same language the user speaks to you.
            
            You can help users with:
            - Looking up their policy details from the CRM
            - Updating their address or vehicle registration plate  
            - Creating support tickets in HubSpot for any issue
            - Filing insurance claims
            
            WHEN TO CREATE A TICKET:
            - When the user asks to create, raise, or file a ticket
            - When there's an issue that needs follow-up
            - When the user has a complaint or problem to report
            Use the raise_support_ticket tool with a subject and description.
            
            IMPORTANT RULES:
            - Keep your responses concise, empathetic, and professional.
            - NEVER output function/tool call syntax in your speech. Just speak naturally.
            - When you need information from the user, simply ask for it in plain language.
            - When calling a tool, do NOT say the tool name or parameters out loud.
            - ALWAYS confirm back to the user after completing an action. For example:
              * "I've updated your address to [new address]"
              * "Your registration plate has been changed to [plate number] and your insured vehicle to [make and model]"
              * "I've created a support ticket for you, your reference number is [number]"
            - When updating a registration plate, ALWAYS ask for BOTH the plate number AND the vehicle make/model.
            - If the user switches language mid-conversation, switch with them.
            
            TRANSFER TO HUMAN:
            - If the user explicitly asks to speak with a human agent, use the transfer_to_human tool.
            - Before transferring, let them know you're connecting them to a human representative.
            - Only transfer if they specifically request it or if you genuinely cannot help them.
            
            If the user needs help with claims, you can transfer them to a Claims Specialist."""
        )
        self.hubspot = hubspot_client
        self.hubspot_state = hubspot_state or {}
        self._room = room  # Store room reference for transfer functionality

    def _get_contact_id(self) -> str | None:
        """Get contact_id from async-loaded state."""
        return self.hubspot_state.get('contact_id')

    @function_tool
    async def get_policy_info(
        self, 
        context: RunContext,
        include_details: Annotated[bool, "Whether to include full policy details. Defaults to True."] = True
    ) -> str:
        """Get the customer's policy information from the CRM (HubSpot)."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "I'm sorry, I don't have access to your account information right now."

        logger.info(f"Fetching policy info for contact {contact_id}")
        props = await self.hubspot.get_contact_policy_info(contact_id)
        
        if props:
            policy_info = props.get("policy_info", "")
            name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
            
            if policy_info:
                return f"Here's the policy information for {name}: {policy_info}"
            else:
                return f"I found your account ({name}), but there's no policy information on file yet."
        else:
            return "I couldn't retrieve your policy information. Please try again later."

    @function_tool
    async def update_address(
        self, 
        context: RunContext, 
        city: Annotated[str, "The city name"], 
        country: Annotated[str, "The country name"], 
        postal_code: Annotated[str, "The postal code or zip code"], 
        street_address: Annotated[str, "The street address"]
    ) -> str:
        """Update the user's address in the CRM (HubSpot)."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "I'm sorry, I don't have access to the CRM right now to update your address."

        # Sanitize all inputs
        city = sanitize_input(city)
        country = sanitize_input(country)
        postal_code = sanitize_input(postal_code, max_length=20)
        street_address = sanitize_input(street_address, max_length=300)
        
        logger.info(f"Updating address for {contact_id}: {city}, {country}, {postal_code}, {street_address}")
        success = await self.hubspot.update_contact_address(contact_id, {
            "city": city,
            "country": country,
            "postalCode": postal_code,
            "streetAddress": street_address
        })
        
        if success:
            return "I've updated your address in our system."
        else:
            return "I encountered an issue updating your address. Please try again later."

    @function_tool
    async def update_registration_plate(
        self, 
        context: RunContext, 
        plate_number: Annotated[str, "The vehicle registration plate number (e.g., 'ABC 123', 'XY12 ABC')"],
        vehicle_make_model: Annotated[str, "The vehicle make and model (e.g., 'BMW 3 Series', 'Toyota Corolla', 'Ford Focus')"]
    ) -> str:
        """Update the user's vehicle registration plate and insured vehicle in the CRM (HubSpot). Always ask for both the plate number AND the vehicle make/model."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "I'm sorry, I don't have access to the CRM right now to update your registration plate."

        # Sanitize inputs
        plate_number = sanitize_input(plate_number, max_length=20).upper()
        vehicle_make_model = sanitize_input(vehicle_make_model, max_length=100)
        
        logger.info(f"Updating registration plate for {contact_id}: {plate_number}, vehicle: {vehicle_make_model}")
        success = await self.hubspot.update_registration_plate(contact_id, plate_number, vehicle_make_model)
        
        if success:
            return f"I've updated your vehicle registration plate to {plate_number} and your insured vehicle to {vehicle_make_model} in our system."
        else:
            return "I encountered an issue updating your registration plate. Please try again later."

    @function_tool
    async def raise_support_ticket(
        self, 
        context: RunContext,
        subject: Annotated[str, "Brief subject/title for the ticket"],
        description: Annotated[str, "Detailed description of the issue"],
        priority: Annotated[str, "Priority level: LOW, MEDIUM, or HIGH. Use MEDIUM if not specified."]
    ) -> str:
        """Raise a support ticket in the CRM system for follow-up."""
        contact_id = self._get_contact_id()
        if not self.hubspot:
            return "I'm sorry, I can't create a ticket right now. Please try again later."

        # Sanitize inputs
        subject = sanitize_input(subject, max_length=100)
        description = sanitize_input(description, max_length=2000)
        priority = sanitize_input(priority, max_length=10).upper()
        if priority not in ["LOW", "MEDIUM", "HIGH"]:
            priority = "MEDIUM"
        
        logger.info(f"Creating ticket: {subject} (Priority: {priority})")
        ticket = await self.hubspot.create_ticket(
            subject=subject,
            description=description,
            priority=priority,
            contact_id=contact_id
        )
        
        if ticket:
            ticket_id = ticket.get("id", "unknown")
            return f"I've created a support ticket for you. Your ticket number is {ticket_id}. Our team will follow up with you soon."
        else:
            return "I encountered an issue creating the ticket. Please try again or contact support directly."

    @function_tool
    async def get_current_time(
        self, 
        context: RunContext,
        timezone: Annotated[str, "Timezone name (e.g., 'UTC', 'Europe/London'). Defaults to local time if not specified."] = "local"
    ) -> str:
        """Get the current date and time."""
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        return f"The current date and time is {current_datetime}"

    @function_tool
    async def transfer_to_human(
        self,
        context: RunContext,
        reason: Annotated[str, "Brief reason for the transfer (e.g., 'customer requested human agent', 'complex issue')"]
    ) -> str:
        """
        Transfer the call to a human agent via phone.
        Use this when the customer explicitly asks to speak with a human representative.
        IMPORTANT: Only use this for SIP/phone calls, not web-based voice calls.
        """
        # Get the phone number to transfer to from environment
        transfer_phone = os.getenv("TRANSFER_PHONE_NUMBER")
        
        if not transfer_phone:
            logger.warning("TRANSFER_PHONE_NUMBER not configured")
            return "I'm sorry, I'm unable to transfer you to a human agent at this moment. Please call our main support line directly, or I can create a support ticket for a callback."
        
        # Get room and participant info from stored room reference
        room_name = None
        participant_identity = None
        
        if self._room:
            room_name = self._room.name
            # Find the first non-agent remote participant (the user)
            for participant in self._room.remote_participants.values():
                if participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                    participant_identity = participant.identity
                    break
        
        if not room_name or not participant_identity:
            logger.warning(f"Missing room_name ({room_name}) or participant_identity ({participant_identity}) for transfer")
            return "I'm sorry, I'm unable to transfer you at this moment. Would you like me to create a support ticket for a callback instead?"
        
        logger.info(f"Initiating transfer to human: {transfer_phone} (reason: {reason})")
        
        try:
            # Use LiveKit API to transfer the SIP participant
            async with api.LiveKitAPI() as livekit_api:
                transfer_request = TransferSIPParticipantRequest(
                    participant_identity=participant_identity,
                    room_name=room_name,
                    transfer_to=f"tel:{transfer_phone}",
                    play_dialtone=True
                )
                
                await livekit_api.sip.transfer_sip_participant(transfer_request)
                logger.info(f"Transfer initiated successfully to {transfer_phone}")
                
            return "I'm transferring you to a human representative now. Please hold while I connect you."
            
        except Exception as e:
            logger.error(f"Failed to transfer call: {type(e).__name__}: {e}")
            return "I apologize, but I wasn't able to transfer your call at this moment. Would you like me to create a support ticket for a callback instead?"
