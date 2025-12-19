"""
Agent Configuration
===================
Shared configuration for voice agents - VAD, logging, etc.
"""

import logging
from livekit.plugins import silero

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log")
    ]
)

# Pre-load VAD model at module level for faster startup
logger = logging.getLogger("agent-config")
logger.info("Pre-loading Silero VAD model...")
PRELOADED_VAD = silero.VAD.load()
logger.info("VAD model pre-loaded successfully")
