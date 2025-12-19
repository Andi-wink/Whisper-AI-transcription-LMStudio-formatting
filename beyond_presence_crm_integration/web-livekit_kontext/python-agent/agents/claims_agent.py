"""
Claims Agent
=============
Specialized agent for handling insurance claims.
"""

from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool
from datetime import datetime
from typing import Annotated
import logging

logger = logging.getLogger("claims-agent")


class ClaimsAgent(Agent):
    """Specialized Claims Agent for handling insurance claims."""

    # Different voice for Claims Agent - "British Narration Man" (mature male voice)
    CLAIMS_VOICE_ID = "a0e99841-438c-4a64-b679-ae501e7d6091"

    def __init__(self, hubspot_client=None, hubspot_state=None, chat_ctx=None):
        super().__init__(
            instructions="""You are a specialized Claims Agent for an insurance company.
            Your role is to help customers file and track insurance claims.
            You can:
            - Help file new claims
            - Check claim status
            - Explain the claims process
            - Escalate complex claims to the support team
            
            Be empathetic and thorough - claims can be stressful for customers.
            Ask clarifying questions to ensure accurate claim filing.""",
            chat_ctx=chat_ctx,  # Preserve conversation history from handoff
            tts=f"cartesia/sonic-turbo:{self.CLAIMS_VOICE_ID}"  # Different voice
        )
        self.hubspot = hubspot_client
        self.hubspot_state = hubspot_state
        
        # Track claims in session
        self.claims = []

    async def on_enter(self) -> None:
        """Called when this agent takes control of the session."""
        await self.session.generate_reply(
            instructions="Introduce yourself as a Claims Specialist. Acknowledge the transfer and ask how you can help with their claim."
        )

    def _get_contact_id(self) -> str | None:
        """Get contact_id from async-loaded state."""
        if self.hubspot_state:
            return self.hubspot_state.get('contact_id')
        return None

    @function_tool
    async def file_claim(
        self, 
        context: RunContext, 
        policy_id: Annotated[str, "The policy ID associated with the claim"],
        incident_type: Annotated[str, "Type of incident (e.g., 'auto accident', 'property damage', 'theft')"],
        incident_description: Annotated[str, "Detailed description of what happened"],
        incident_date: Annotated[str, "The date the incident occurred (e.g., 'November 28, 2024')"]
    ) -> str:
        """File a new insurance claim with detailed information."""
        claim = {
            "claim_number": f"CLM{len(self.claims) + 2001}",
            "policy_id": policy_id,
            "type": incident_type,
            "description": incident_description,
            "date": incident_date,
            "status": "Submitted",
            "filed_at": datetime.now().isoformat()
        }
        
        self.claims.append(claim)
        logger.info(f"Filed claim {claim['claim_number']} for policy {policy_id}")

        result = f"I've filed your claim successfully.\n\n"
        result += f"Claim Number: {claim['claim_number']}\n"
        result += f"Type: {claim['type']}\n"
        result += f"Policy: {claim['policy_id']}\n"
        result += f"Date of Incident: {claim['date']}\n"
        result += f"Status: {claim['status']}\n\n"
        result += "A claims adjuster will review your case and contact you within 24-48 hours."

        return result

    @function_tool
    async def check_claim_status(
        self, 
        context: RunContext,
        claim_number: Annotated[str, "The claim number to check (e.g., 'CLM2001')"]
    ) -> str:
        """Check the status of an existing claim."""
        # Check in-session claims
        for claim in self.claims:
            if claim["claim_number"] == claim_number:
                return f"Claim {claim_number} is currently '{claim['status']}'. Filed on {claim['date']} for policy {claim['policy_id']}."
        
        # Mock response for demo
        return f"I couldn't find claim {claim_number} in our system. Please verify the claim number or it may still be processing."

    @function_tool
    async def explain_claims_process(
        self, 
        context: RunContext,
        claim_type: Annotated[str, "Type of claim to explain (e.g., 'auto', 'home', 'life', 'general')"]
    ) -> str:
        """Explain the insurance claims process to the customer."""
        process = """Here's how our claims process works:

1. **Filing**: You provide the incident details (which we just did or can do now)
2. **Review**: A claims adjuster reviews your case within 24-48 hours
3. **Investigation**: We may contact you for additional information or documentation
4. **Assessment**: We evaluate the damage and coverage
5. **Resolution**: We process the payment or explain next steps

Throughout this process, you can check your claim status anytime by calling us or using our app."""
        
        return process

    @function_tool
    async def transfer_to_support(
        self, 
        context: RunContext,
        reason: Annotated[str, "Reason for transferring back to support"]
    ):
        """Transfer the customer back to the main support agent for non-claims questions."""
        from agents.support_agent import SupportAgent
        
        logger.info(f"Transferring back to Support Agent. Reason: {reason}")
        return SupportAgent(
            hubspot_client=self.hubspot,
            hubspot_state=self.hubspot_state,
            chat_ctx=self.chat_ctx
        ), "Transferring you back to our support team."
