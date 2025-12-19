import asyncio
import logging
import os
import time
import numpy as np
from typing import AsyncIterable, List, Optional

from livekit import agents
from livekit.agents import stt, tts, utils
from livekit.rtc import AudioFrame

# Try importing local dependencies
if os.name == 'nt':
    import site
    site_packages = site.getsitepackages()
    for sp in site_packages:
        nvidia_base = os.path.join(sp, 'nvidia')
        if os.path.exists(nvidia_base):
             for root, dirs, files in os.walk(nvidia_base):
                 if 'bin' in dirs:
                     os.environ['PATH'] = os.path.join(root, 'bin') + os.pathsep + os.environ['PATH']

try:
    from faster_whisper import WhisperModel
except ImportError:
    logging.warning("faster-whisper not installed. Local STT will not work.")

try:
    from melo.api import TTS as MeloTTSWrapper
except ImportError as e:
    logging.warning(f"melotts not installed: {e}. Local TTS will not work.")
except Exception as e:
    logging.warning(f"Error importing melotts: {e}")

logger = logging.getLogger("local-plugins")

class LocalWhisperSTT(stt.STT):
    def __init__(self, model_size: str = "base", device: str = "auto", compute_type: str = "default"):
        super().__init__(capabilities=stt.STTCapabilities(streaming=False, interim_results=False))
        logger.info(f"Loading Faster-Whisper model: {model_size} on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Faster-Whisper model loaded.")

    async def recognize(self, buffer: utils.AudioBuffer, language: str = None):
        # Convert buffer to numpy array (16-bit PCM to float32)
        data = np.frombuffer(buffer.data, dtype=np.int16).flatten().astype(np.float32) / 32768.0
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(None, 
            lambda: self.model.transcribe(data, language=language, beam_size=5))
        
        # self.model.transcribe returns a generator, so we need to iterate it to get text
        # But we can't iterate a generator created in a thread easily if it relies on thread-local state (which whisper might not, but safer to consume in thread)
        def transcribe_sync():
            segs, inf = self.model.transcribe(data, language=language, beam_size=5)
            return list(segs), inf
            
        segments_list, info = await loop.run_in_executor(None, transcribe_sync)
        text = " ".join([s.text for s in segments_list])
        
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[stt.SpeechData(text=text, confidence=1.0, language=info.language)],
            is_final=True
        )

class LocalMeloTTS(tts.TTS):
    def __init__(self, language: str = "EN", device: str = "auto"):
        super().__init__(capabilities=tts.TTSCapabilities(streaming=False), sample_rate=44100, num_channels=1)
        logger.info(f"Loading MeloTTS model for language: {language}...")
        self.model = MeloTTSWrapper(language=language, device=device)
        self.speaker_ids = self.model.hps.data.spk2id
        logger.info("MeloTTS model loaded.")

    def synthesize(self, text: str) -> "ChunkedStream":
        return LocalMeloTTSStream(self.model, text, self.speaker_ids)

class LocalMeloTTSStream(tts.ChunkedStream):
    def __init__(self, tts_model, text, speaker_ids):
        super().__init__()
        self.tts_model = tts_model
        self.text = text
        self.speaker_ids = speaker_ids
        self._queue = asyncio.Queue()
        self._run_synthesis()

    def _run_synthesis(self):
        asyncio.create_task(self._synthesize_task())

    async def _synthesize_task(self):
        loop = asyncio.get_event_loop()
        try:
            # MeloTTS tts_to_file returns nothing, but we can use tts_to_audio (if available) or hack it.
            # Looking at MeloTTS API, usually `model.tts_to_file(text, speaker_id, filename)`
            # But we want bytes. Let's check if there is a method to get audio directly.
            # If not, we might need to write to a temp file or check source.
            # Most implementations allow getting numpy array.
            # Assuming `tts_to_file` is the main one, let's see if we can monkeypatch or use internal `infer`.
            
            # Actually, MeloTTS usually has `model.tts(text, speaker_id)` which returns audio_data (numpy)
            # Let's assume standard usage: audio = model.tts(text, speaker_id=speaker_ids['EN-US'])
            
            # Default speaker for EN is usually 'EN-US' or 'EN-Default'
            speaker_id = self.speaker_ids['EN-US']
            
            import tempfile
            import soundfile as sf
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                
            try:
                # Use tts_to_file
                await loop.run_in_executor(None, lambda: self.tts_model.tts_to_file(self.text, speaker_id, temp_path, speed=1.0))
                
                # Read back
                audio_data, sample_rate = sf.read(temp_path)
                
                # audio_data is float32, convert to int16 PCM
                pcm_data = (audio_data * 32767).astype(np.int16).tobytes()
                
                # Create frame
                frame = AudioFrame(data=pcm_data, sample_rate=sample_rate, num_channels=1, samples_per_channel=len(pcm_data)//2)
                self._queue.put_nowait(tts.SynthesizedAudio(frame=frame))
                
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
        except Exception as e:
            logger.error(f"TTS Error: {e}")
        finally:
            self._queue.put_nowait(None)

    async def __anext__(self) -> tts.SynthesizedAudio:
        item = await self._queue.get()
        if item is None:
            raise StopAsyncIteration
        return item
