"""
Insurance Tools
===============
Voice agent tools for insurance operations - policy lookup, claims, CRM updates.
"""

import os
import aiohttp
from livekit import api
from livekit.agents import Agent, RunContext, get_job_context
from livekit.agents.llm import function_tool
from datetime import datetime, timedelta
from typing import Annotated
import logging

logger = logging.getLogger("insurance-support-agent")

# SIP Transfer configuration
TRANSFER_PHONE_NUMBER = os.getenv("TRANSFER_PHONE_NUMBER", "+353896123639")
OUTBOUND_TRUNK_ID = os.getenv("OUTBOUND_TRUNK_ID", "ST_YF2FRpx7F7Qw")

# N8N Webhook for call summaries
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")


class InsuranceAssistant(Agent):
    """Voice assistant with Insurance capabilities and HubSpot integration."""

    def __init__(self, hubspot_client=None, contact_id: str = None):
        super().__init__(
            instructions="""You are a helpful and professional Insurance Support Agent for U-insure.
            You can help users with:
            - Looking up their policy details from the CRM
            - Filing insurance claims
            - Updating their address or vehicle registration plate
            - Raising support tickets for issues that need follow-up
            - Transferring them to a human agent ONLY when explicitly requested
            
            IMPORTANT RULES:
            1. Only use the transfer_call tool if the user EXPLICITLY asks to speak to a human, real person, or representative.
               Do NOT transfer the call unless the user clearly requests it with phrases like "transfer me", "speak to a human", "real person please", etc.
            2. When the user says goodbye, thanks you and ends the call, or the conversation is clearly ending, 
               use the send_call_summary tool to record a summary of the call.
            
            Keep your responses concise, empathetic, and professional."""
        )
        self.hubspot = hubspot_client
        self.contact_id = contact_id
        self.hubspot_state = None  # Will be set by entrypoint for async loading

        # Mock Insurance database
        self.policies = {
            "12345": {
                "id": "12345",
                "holder": "Harrison Scott",
                "type": "Auto Insurance",
                "coverage": "Full Coverage",
                "status": "Active",
                "deductible": 500,
            },
            "67890": {
                "id": "67890",
                "holder": "Jane Smith",
                "type": "Home Insurance",
                "coverage": "Dwelling & Personal Property",
                "status": "Active",
                "deductible": 1000,
            },
            "54321": {
                "id": "54321",
                "holder": "Bob Johnson",
                "type": "Life Insurance",
                "coverage": "Term Life 20 Years",
                "status": "Active",
                "beneficiary": "Alice Johnson",
            }
        }

        # Track claims
        self.claims = []

    def _get_contact_id(self) -> str | None:
        """Get contact_id from async-loaded state or direct assignment."""
        if self.hubspot_state:
            return self.hubspot_state.get('contact_id')
        return self.contact_id

    @function_tool
    async def transfer_call(self, context: RunContext) -> str:
        """Transfer the call to a human agent. Use this tool when the user asks to speak to a human, real person, representative, or wants to be transferred."""
        logger.info("TOOL CALLED: transfer_call invoked!")
        
        await context.session.generate_reply(
            instructions="Tell the user you are now connecting them to a human representative and ask them to please hold."
        )
        
        job_ctx = get_job_context()
        logger.info(f"Transfer requested - Room: {job_ctx.room.name}, Trunk: {OUTBOUND_TRUNK_ID}, Phone: {TRANSFER_PHONE_NUMBER}")
        
        try:
            participant = await job_ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=OUTBOUND_TRUNK_ID,
                    sip_call_to=TRANSFER_PHONE_NUMBER,
                    room_name=job_ctx.room.name,
                    participant_identity="human-support",
                    participant_name="Human Support Agent",
                    krisp_enabled=True,
                    play_dialtone=True,
                    ringing_timeout=timedelta(seconds=60),  # Ring for up to 60 seconds
                )
            )
            logger.info(f"SUCCESS: Dialing {TRANSFER_PHONE_NUMBER} - participant: {participant}")
            return "Human support agent is being connected to the call. Please hold."
        except Exception as e:
            import traceback
            logger.error(f"TRANSFER FAILED: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return f"I'm sorry, I couldn't connect you to a human agent right now. Please try calling back later or use our support email."

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
        plate_number: Annotated[str, "The vehicle registration plate number (e.g., 'ABC 123', 'XY12 ABC')"]
    ) -> str:
        """Update the user's vehicle registration plate in the CRM (HubSpot)."""
        contact_id = self._get_contact_id()
        if not self.hubspot or not contact_id:
            return "I'm sorry, I don't have access to the CRM right now to update your registration plate."

        logger.info(f"Updating registration plate for {contact_id}: {plate_number}")
        success = await self.hubspot.update_registration_plate(contact_id, plate_number)
        
        if success:
            return f"I've updated your vehicle registration plate to {plate_number} in our system."
        else:
            return "I encountered an issue updating your registration plate. Please try again later."

    @function_tool
    async def get_current_date_and_time(
        self, 
        context: RunContext,
        timezone: Annotated[str, "Optional timezone name (e.g., 'UTC', 'EST'). Defaults to local time."] = "local"
    ) -> str:
        """Get the current date and time.
        
        Args:
            timezone: Optional timezone name. Defaults to local time.
        """
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        return f"The current date and time is {current_datetime}"

    @function_tool
    async def get_policy_info_from_crm(
        self, 
        context: RunContext,
        confirm: Annotated[str, "Say 'yes' to confirm fetching policy info"] = "yes"
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
    async def raise_support_ticket(
        self, 
        context: RunContext,
        subject: Annotated[str, "Brief subject/title for the ticket (e.g., 'Claim inquiry', 'Policy question')"],
        description: Annotated[str, "Detailed description of the issue or request"],
        priority: Annotated[str, "Priority level: LOW, MEDIUM, or HIGH"] = "MEDIUM"
    ) -> str:
        """Raise a support ticket in the CRM system for follow-up by the support team."""
        contact_id = self._get_contact_id()
        if not self.hubspot:
            return "I'm sorry, I can't create a ticket right now. Please try again later."

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
    async def lookup_policy(
        self, 
        context: RunContext, 
        policy_id: Annotated[str, "The policy ID to search for (e.g., '12345', '67890')"]
    ) -> str:
        """Look up insurance policy details."""
        if policy_id not in self.policies:
            return f"Sorry, I couldn't find a policy with ID {policy_id}. Please check the number and try again."

        policy = self.policies[policy_id]
        result = f"Policy Details for {policy_id}:\n"
        result += f"• Holder: {policy['holder']}\n"
        result += f"• Type: {policy['type']}\n"
        result += f"• Coverage: {policy['coverage']}\n"
        result += f"• Status: {policy['status']}\n"
        result += f"• Deductible: ${policy['deductible']}\n"

        return result

    @function_tool
    async def file_claim(
        self, 
        context: RunContext, 
        policy_id: Annotated[str, "The policy ID associated with the claim"],
        incident_description: Annotated[str, "A brief description of what happened"],
        incident_date: Annotated[str, "The date the incident occurred"]
    ) -> str:
        """File a new insurance claim."""
        if policy_id not in self.policies:
            return f"Sorry, I cannot file a claim for policy ID {policy_id} because it was not found."

        # Create claim
        claim = {
            "claim_number": f"CLM{len(self.claims) + 1001}",
            "policy_id": policy_id,
            "description": incident_description,
            "date": incident_date,
            "status": "Submitted",
        }

        self.claims.append(claim)

        result = f"✓ Claim filed successfully!\n\n"
        result += f"Claim Number: {claim['claim_number']}\n"
        result += f"Policy ID: {claim['policy_id']}\n"
        result += f"Description: {claim['description']}\n"
        result += f"Date: {claim['date']}\n"
        result += f"Status: {claim['status']}\n\n"
        result += f"An adjuster will review your claim and contact you within 24-48 hours."

        return result

    @function_tool
    async def send_call_summary(
        self, 
        context: RunContext,
        summary: Annotated[str, "A brief summary of the call conversation and key points discussed"],
        customer_sentiment: Annotated[str, "The customer's sentiment: positive, neutral, or negative"] = "neutral",
        follow_up_required: Annotated[bool, "Whether follow-up action is required"] = False,
        actions_taken: Annotated[str, "List of actions taken during the call (e.g., 'Updated address', 'Filed claim')"] = ""
    ) -> str:
        """Send a call summary to the CRM/n8n webhook at the end of a call. Use this when the call is ending or the user says goodbye."""
        if not N8N_WEBHOOK_URL:
            logger.warning("N8N_WEBHOOK_URL not configured - call summary not sent")
            return "Call summary noted but webhook not configured."

        contact_id = self._get_contact_id()
        job_ctx = get_job_context()
        
        payload = {
            "timestamp": datetime.now().isoformat(),
            "room_name": job_ctx.room.name if job_ctx else "unknown",
            "contact_id": contact_id,
            "summary": summary,
            "customer_sentiment": customer_sentiment,
            "follow_up_required": follow_up_required,
            "actions_taken": actions_taken,
            "agent_name": "U-insure Support Agent"
        }

        logger.info(f"TOOL CALLED: send_call_summary - Sending to {N8N_WEBHOOK_URL}")
        logger.info(f"Call summary payload: {payload}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(N8N_WEBHOOK_URL, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"SUCCESS: Call summary sent to n8n webhook")
                        return "Call summary has been sent to the CRM system."
                    else:
                        logger.error(f"FAILED: n8n webhook returned status {response.status}")
                        return f"Failed to send call summary (status {response.status})."
        except Exception as e:
            logger.error(f"FAILED: Error sending call summary: {e}")
            return f"Failed to send call summary: {str(e)}"
