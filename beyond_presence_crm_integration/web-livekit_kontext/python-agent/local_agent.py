import logging
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, JobContext, WorkerOptions
from livekit.plugins import openai, silero
from livekit.agents.llm import LLM

# Import our local plugins
from local_plugins import LocalWhisperSTT, LocalMeloTTS

load_dotenv(".env")
load_dotenv(".env.local")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local-agent")

async def entrypoint(ctx: JobContext):
    logger.info("Starting local agent with MeloTTS...")

    # 1. Setup Local LLM (Ollama)
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    ollama_model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    
    llm = openai.LLM(
        base_url=ollama_base_url,
        model=ollama_model,
        api_key="ollama",
    )

    # 2. Setup Local STT (Faster-Whisper)
    stt = LocalWhisperSTT(model_size="base.en", device="auto")

    # 3. Setup Local TTS (MeloTTS)
    # Using 'auto' device will use GPU if available
    tts = LocalMeloTTS(language="EN", device="auto")

    # 4. Setup VAD
    vad = silero.VAD.load()

    # Create the session
    session = AgentSession(
        stt=stt,
        llm=llm,
        tts=tts,
        vad=vad,
    )

    # Define the agent
    agent = agents.Agent(
        instructions="You are a helpful local assistant running entirely on open source models.",
    )

    # Start the session
    await session.start(room=ctx.room, agent=agent)

    # Initial greeting
    await session.generate_reply(instructions="Say hello and mention that you are running locally with MeloTTS.")

if __name__ == "__main__":
    agents.cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
