"""
Call Summary Integration
========================
Collects transcript during call and sends summary to n8n webhook at call end.
"""

import aiohttp
import logging
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger("call-summary")


@dataclass
class TranscriptMessage:
    """A single message in the transcript."""
    sender: str  # "ai" or "user"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class CallSummaryCollector:
    """Collects call transcript and sends summary to n8n at call end."""
    
    def __init__(
        self,
        call_id: str,
        user_name: str = "Andrew Winkler",
        user_email: str = "andrew@automationmatters.org",
        webhook_url: Optional[str] = None
    ):
        self.call_id = call_id
        self.user_name = user_name
        self.user_email = user_email
        self.webhook_url = webhook_url or os.getenv("N8N_WEBHOOK_URL")
        self.transcript: List[TranscriptMessage] = []
        self.call_start = datetime.utcnow()
        
    def add_user_message(self, content: str):
        """Add a user message to the transcript."""
        self.transcript.append(TranscriptMessage(sender="user", content=content))
        logger.debug(f"Transcript: [user] {content}")
        
    def add_ai_message(self, content: str):
        """Add an AI message to the transcript."""
        self.transcript.append(TranscriptMessage(sender="ai", content=content))
        logger.debug(f"Transcript: [ai] {content}")
    
    def get_full_transcript_text(self) -> str:
        """Get the full transcript as formatted text."""
        lines = []
        for msg in self.transcript:
            lines.append(f"[{msg.sender}] {msg.content}")
        return "\n".join(lines)
    
    def analyze_sentiment(self) -> str:
        """Simple sentiment analysis based on transcript content."""
        text = self.get_full_transcript_text().lower()
        
        positive_words = [
            "thank", "thanks", "great", "excellent", "perfect", "wonderful",
            "appreciate", "helpful", "good", "happy", "pleased", "satisfied",
            "awesome", "fantastic", "love", "best", "amazing"
        ]
        negative_words = [
            "frustrated", "angry", "upset", "terrible", "horrible", "bad",
            "disappointing", "unhappy", "annoyed", "complaint", "problem",
            "issue", "wrong", "hate", "worst", "awful", "useless"
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count + 1:
            return "positive"
        elif negative_count > positive_count + 1:
            return "negative"
        else:
            return "neutral"
    
    def get_call_duration_seconds(self) -> int:
        """Get call duration in seconds."""
        return int((datetime.utcnow() - self.call_start).total_seconds())
    
    async def send_summary(self) -> bool:
        """Send call summary to n8n webhook."""
        if not self.webhook_url:
            logger.warning("N8N_WEBHOOK_URL not set - skipping call summary")
            return False
        
        if not self.transcript:
            logger.info("No transcript to send - call may have been too short")
            return False
        
        payload = {
            "event_type": "call_ended",
            "call_id": self.call_id,
            "user_name": self.user_name,
            "user_email": self.user_email,
            "transcript": [
                {
                    "sender": msg.sender,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in self.transcript
            ],
            "full_transcript_text": self.get_full_transcript_text(),
            "sentiment": self.analyze_sentiment(),
            "call_duration_seconds": self.get_call_duration_seconds(),
            "call_start": self.call_start.isoformat(),
            "call_end": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Sending call summary to n8n: {self.call_id}")
        logger.info(f"Transcript: {len(self.transcript)} messages, Sentiment: {payload['sentiment']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Call summary sent successfully: {self.call_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send call summary: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error sending call summary: {e}")
            return False


def setup_call_summary(session, room, collector: CallSummaryCollector):
    """
    Set up event handlers to collect transcript and send summary.
    
    Args:
        session: The AgentSession
        room: The LiveKit room
        collector: The CallSummaryCollector instance
    """
    
    @session.on("conversation_item_added")
    def on_conversation_item(event):
        """Capture both user and agent messages."""
        try:
            role = event.item.role  # "user" or "assistant"
            text = event.item.text_content
            
            if text:
                if role == "user":
                    collector.add_user_message(text)
                    logger.debug(f"Captured user: {text[:50]}...")
                elif role == "assistant":
                    collector.add_ai_message(text)
                    logger.debug(f"Captured agent: {text[:50]}...")
        except Exception as e:
            logger.error(f"Error capturing conversation item: {e}")
    
    @room.on("participant_disconnected")
    def on_participant_left(participant):
        """Send summary when USER leaves (not agents/avatars)."""
        # Skip avatar and agent participants
        if "avatar" in participant.identity.lower() or "agent" in participant.identity.lower():
            logger.debug(f"Ignoring disconnect from avatar/agent: {participant.identity}")
            return
        
        # Also check participant kind - skip if it's an agent
        from livekit import rtc
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
            logger.debug(f"Ignoring disconnect from agent participant: {participant.identity}")
            return
            
        logger.info(f"User disconnected: {participant.identity}")
        import asyncio
        asyncio.create_task(collector.send_summary())
    
    logger.info(f"Call summary collector initialized for room: {collector.call_id}")
