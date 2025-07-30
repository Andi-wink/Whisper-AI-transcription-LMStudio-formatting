import tkinter as tk
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import time
import pyperclip
import re
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline, GenerationConfig
import keyboard
from Local_AI_server import send_transcription  # Import the server-side function
from tkinter import filedialog
import threading
import traceback
from pydub import AudioSegment
import numpy as np
import io
from PIL import Image, ImageTk, ImageDraw
import queue
import webrtcvad  # For voice activity detection

# Import win32 modules with proper error handling
try:
    import win32clipboard
    from win32con import CF_DIB, CF_UNICODETEXT, CF_BITMAP
    win32_available = True
except ImportError:
    print("Warning: win32clipboard module not available. Image clipboard functionality will be limited.")
    win32_available = False

# Set device to GPU if available
print("\n=== CUDA Diagnostic Information ===")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda if torch.cuda.is_available() else 'Not available'}")

if not torch.cuda.is_available():
    print("\nCUDA is not available. Checking possible reasons:")
    try:
        import nvidia_smi
        nvidia_smi.nvmlInit()
        print("NVIDIA driver is installed")
        device_count = nvidia_smi.nvmlDeviceGetCount()
        print(f"Number of NVIDIA devices: {device_count}")
        for i in range(device_count):
            handle = nvidia_smi.nvmlDeviceGetHandleByIndex(i)
            info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
            print(f"GPU {i}: {nvidia_smi.nvmlDeviceGetName(handle).decode()}")
            print(f"Memory Total: {info.total / 1024**2:.2f} MB")
            print(f"Memory Free: {info.free / 1024**2:.2f} MB")
    except Exception as e:
        print(f"Could not get NVIDIA driver information: {e}")
        print("Please ensure NVIDIA drivers are installed correctly")

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

if torch.cuda.is_available():
    print(f"\nCUDA Configuration:")
    print(f"CUDA device: {torch.cuda.get_device_name()}")
    print(f"CUDA device count: {torch.cuda.device_count()}")
    print(f"CUDA current device: {torch.cuda.current_device()}")
    print(f"CUDA capability: {torch.cuda.get_device_capability()}")
    print(f"Torch dtype: {torch_dtype}")
else:
    print("\nRunning on CPU")
print("================================\n")

# Load the model
print("Loading Whisper model...")
model_id = "openai/whisper-large-v3"

# Try to ensure CUDA is used if available
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    print(f"GPU memory before model load: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True,
    device_map="auto" if torch.cuda.is_available() else None
)

if torch.cuda.is_available():
    print(f"GPU memory after model load: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
    print(f"Model device: {next(model.parameters()).device}")

model.to(device)
print(f"Model loaded and moved to {device}")

# Compile the model if using CUDA
if torch.cuda.is_available():
    print("Compiling model for faster inference...")
    try:
        model = torch.compile(model)
        print("Model compilation successful")
    except Exception as e:
        print(f"Warning: Model compilation failed: {e}")
        print("Continuing with uncompiled model")

# Initialize the generation config
model.generation_config = GenerationConfig.from_pretrained(model_id)
print("Generation config initialized")

# Load the processor
print("Loading processor...")
processor = AutoProcessor.from_pretrained(model_id)
print("Processor loaded")

# Initialize the pipeline
print("Initializing pipeline...")
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=445,
    chunk_length_s=30,
    batch_size=16,
    return_timestamps=True,
    torch_dtype=torch_dtype,
)
print("Pipeline initialized")

# Create main window with minimalist design
root = tk.Tk()
root.geometry("300x80")  # Much smaller window
root.title("Speech Recorder")
root.configure(background="#1a2b47")  # Dark blue background
root.attributes('-topmost', True)  # Always on top

# Optional: Remove window decorations for even more minimalist look
# root.overrideredirect(True)  # Uncomment to remove title bar

# Create PIL for custom circular buttons

# Initialize states
is_recording = False
is_transcribing = False
recording = None
filename = None
max_duration = 90  # Maximum recording duration in seconds
sample_rate = 16000  # Changed to 16kHz for compatibility with VAD
chunk_duration = 0.03  # 30ms chunks for VAD processing
silence_threshold = 0.5  # Amplitude threshold for silence detection
silence_duration = 7.0  # Stop after 5 seconds of silence
last_button_clicked = None
clipboard_content = None
previous_clipboard = None  # Store the previous clipboard content before transcription
clipboard_format = None  # Store the format of the clipboard content (text or image)
last_clipboard_check = time.time()  # Track when we last checked the clipboard

# Global audio stream reference
audio_stream = None

# Initialize VAD (Voice Activity Detection)
try:
    vad = webrtcvad.Vad(3)  # Aggressiveness level 3 (highest)
    vad_available = True
except Exception as e:
    print(f"Warning: Could not initialize WebRTC VAD: {e}")
    print("Variable-length recording will use amplitude-based detection instead.")
    vad_available = False

# Audio processing queue and thread
audio_queue = queue.Queue()
recording_active = False
silence_counter = 0
audio_chunks = []

def process_audio_chunks():
    """Process audio chunks for voice activity detection."""
    global recording_active, silence_counter, audio_chunks
    
    while recording_active:
        try:
            # Get chunk from queue with timeout
            chunk = audio_queue.get(timeout=0.1)
            audio_chunks.append(chunk)
            
            # Check for voice activity
            has_voice = False
            
            if vad_available:
                # Convert float32 samples to int16 for VAD
                int16_chunk = (chunk * 32767).astype(np.int16).tobytes()
                try:
                    has_voice = vad.is_speech(int16_chunk, sample_rate)
                except Exception:
                    # Fallback to amplitude-based detection if VAD fails
                    has_voice = np.max(np.abs(chunk)) > silence_threshold
            else:
                # Use simple amplitude threshold if VAD not available
                has_voice = np.max(np.abs(chunk)) > silence_threshold
            
            if has_voice:
                silence_counter = 0
            else:
                silence_counter += chunk_duration
                
                # Stop recording after silence_duration seconds of silence
                if silence_counter >= silence_duration:
                    print(f"Detected {silence_duration}s of silence, stopping recording")
                    recording_active = False
                    
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in audio processing: {e}")
    
    # Signal main thread to stop recording
    if not recording_active and is_recording:
        root.after(0, stop_recording)

def audio_callback(indata, frames, time_info, status):
    """Callback for audio stream to process chunks in real-time."""
    if status:
        print(f"Audio callback status: {status}")
    
    # Put audio chunk in queue for processing
    try:
        audio_queue.put(indata.copy().reshape(-1))
    except queue.Full:
        print("Warning: Audio queue is full, dropping chunk")

def start_recording():
    """Start recording with voice activity detection."""
    global recording, filename, is_recording, recording_active, silence_counter, audio_chunks, audio_stream
    
    if is_recording:
        return  # Already recording
        
    # Reset state
    silence_counter = 0
    audio_chunks = []
    recording_active = True
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
        filename = tf.name
    
    # Start audio processing thread
    audio_thread = threading.Thread(target=process_audio_chunks)
    audio_thread.daemon = True
    audio_thread.start()
    
    # Start audio stream
    try:
        # Close any existing stream first
        if audio_stream is not None:
            try:
                audio_stream.stop()
                audio_stream.close()
            except Exception as e:
                print(f"Warning: Error closing previous stream: {e}")
        
        # Create and start new stream
        audio_stream = sd.InputStream(
            channels=1,
            samplerate=sample_rate,
            blocksize=int(chunk_duration * sample_rate),
            callback=audio_callback
        )
        audio_stream.start()
    except Exception as e:
        print(f"Error starting audio stream: {e}")
        recording_active = False
        return
    
    is_recording = True
    print("Recording started with voice activity detection...")
    
    # Safety timeout - maximum recording duration
    root.after(max_duration * 1000, lambda: stop_recording() if is_recording else None)

def stop_recording():
    """Stop recording."""
    global is_recording, filename, recording_active, audio_stream
    
    if not is_recording:
        return
    
    # Stop the recording stream and thread
    recording_active = False
    
    # Properly close the audio stream
    try:
        if audio_stream is not None:
            audio_stream.stop()
            audio_stream.close()
    except Exception as e:
        print(f"Warning: Error closing audio stream: {e}")
    
    is_recording = False
    
    # Combine all audio chunks
    if audio_chunks and len(audio_chunks) > 0:
        combined_audio = np.concatenate(audio_chunks)
        
        # ENHANCEMENT: Audio volume normalization and amplification
        if len(combined_audio) > 0:
            # Calculate the maximum absolute amplitude
            max_amplitude = np.max(np.abs(combined_audio))
            if max_amplitude > 0:
                # Check if audio is too quiet
                if max_amplitude < 0.2:
                    print(f"Audio volume is low (max amplitude: {max_amplitude:.4f}), applying amplification")
                    gain_factor = 1.8 / max_amplitude
                    combined_audio = combined_audio * gain_factor
                    print(f"Applied gain factor of {gain_factor:.2f}x")
                else:
                    # Standard boost for all audio
                    gain_factor = 2.0
                    combined_audio = np.clip(combined_audio * gain_factor, -1.0, 1.0)
                    print(f"Applied standard boost of {gain_factor:.2f}x to all audio")
            else:
                print("Warning: Recording appears to be silent (max amplitude: 0)")
                
            # Trim silence from the end
            if len(combined_audio) > sample_rate * 0.5:  # At least 0.5 seconds
                # Find the last significant audio
                window_size = int(0.03 * sample_rate)  # 30ms window
                energy = []
                
                for i in range(0, len(combined_audio) - window_size, window_size):
                    window = combined_audio[i:i+window_size]
                    energy.append(np.mean(np.abs(window)))
                
                # Find the last point where energy is above threshold
                threshold = max(np.mean(energy) * 0.1, 0.01)
                last_sound_idx = len(energy) - 1
                
                while last_sound_idx > 0 and energy[last_sound_idx] < threshold:
                    last_sound_idx -= 1
                
                # Add a small buffer after the last sound
                buffer_frames = int(0.5 * sample_rate)  # 0.5 second buffer
                end_frame = min((last_sound_idx + 1) * window_size + buffer_frames, len(combined_audio))
                
                # Trim the audio
                combined_audio = combined_audio[:end_frame]
                print(f"Trimmed audio from {len(audio_chunks) * chunk_duration:.2f}s to {len(combined_audio) / sample_rate:.2f}s")
        
        # Save the processed audio
        sf.write(filename, combined_audio, sample_rate)
        print(f"Recording saved to {filename} (duration: {len(combined_audio) / sample_rate:.2f}s)")
        
        # Process the recording
        handle_transcription()
    else:
        print("No audio recorded or recording too short")

def handle_transcription():
    """Handle transcription based on last_button_clicked."""
    global is_transcribing
    if is_transcribing:
        return
    is_transcribing = True
    try:
        if last_button_clicked == "command":
            transcribe_and_send("command")
        elif last_button_clicked == "notes":
            create_notes_from_transcription()
        elif last_button_clicked == "record":
            transcribe_and_send("record")
        elif last_button_clicked == "transcribe_paste":
            transcribe_and_paste()
        elif last_button_clicked == "transcribe_paste_with_previous":
            transcribe_and_paste_with_previous()
        elif last_button_clicked == "select_file":
            transcribe_and_send("select_file")
        elif last_button_clicked == "email":
            transcribe_and_send_email()
    finally:
        is_transcribing = False

def toggle_recording(button_type):
    """Toggle recording state and update last_button_clicked."""
    global last_button_clicked, clipboard_content

    if is_recording:
        stop_recording()
    else:
        last_button_clicked = button_type
        if button_type == "command":
            clipboard_content = pyperclip.paste()
            print(f"Clipboard Content: {clipboard_content}")
        start_recording()

    update_button_text(button_type)

def update_button_text(button_type):
    """Update the button text based on current state."""
    global is_recording
    if button_type == "record":
        button.config(text="Stop Recording" if is_recording else "Record")
    elif button_type == "command":
        command_button.config(text="Stop Command Recording" if is_recording else "Command")
    elif button_type == "notes":
        notes_button.config(text="Stop Notes Recording" if is_recording else "Notes")

def remove_you_thank_you(text):
    """Remove trailing 'you' or 'thank you'."""
    pattern = r'(?:\s*(?:you|thank you)[\s\.,;!\?]*)+$'
    text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
    return text

def format_response(response):
    """Format AI response by removing unwanted phrases."""
    unwanted_starts = [
        "Here is the converted text:",
        "Here's the refined text:",
        "Here is the refined text",
        "Here is the refined email text:",
    ]

    for phrase in unwanted_starts:
        if phrase in response:
            response = response.split(phrase, 1)[1].strip()
            break

    return response

def log_memory_usage():
    """Log current GPU memory usage."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**2
        reserved = torch.cuda.memory_reserved() / 1024**2
        print(f"\nGPU Memory Usage:")
        print(f"Allocated: {allocated:.2f} MB")
        print(f"Reserved:  {reserved:.2f} MB\n")

def remove_repetitive_phrases(text):
    """
    Remove repetitive phrases that Whisper tends to hallucinate at the end of transcriptions.
    This happens frequently when the audio cuts off abruptly.
    """
    # If text is too short, skip processing
    if len(text) < 15:
        return text
    
    clean_text = text
    
    # 0. First check for specific problematic patterns like "Subtitles by the Amara.org community"
    amara_pattern = r'(Subtitles by the Amara\.org community[\s\.,!?]*)+'
    if re.search(amara_pattern, clean_text, re.IGNORECASE):
        # Remove all instances of this pattern
        clean_text = re.sub(amara_pattern, '', clean_text, flags=re.IGNORECASE)
        # Also check for "Thank you for watching" at the end
        clean_text = re.sub(r'Thank you for watching\.?$', '', clean_text, flags=re.IGNORECASE)
        return clean_text.strip()
    
    # 1. Check for common ending phrases that often repeat
    common_endings = [
        "thank you for watching",
        "thanks for watching",
        "subtitles by",
        "good luck this week",
        "thank you",
        "amara.org community"
    ]
    
    for ending in common_endings:
        pattern = f"({re.escape(ending)}[\\s\\.,!?]*)+$"
        matches = re.findall(pattern, clean_text.lower())
        if matches:
            # Find the first occurrence and remove all others
            idx = clean_text.lower().find(ending)
            if idx > 0:
                clean_text = clean_text[:idx] + ending.capitalize() + "."
                return clean_text
    
    # 2. Check for short phrases (2-3 words) that repeat
    words = text.split()
    for phrase_length in range(2, 4):  # Short phrases (2-3 words)
        if len(words) < phrase_length * 2:
            continue
            
        for i in range(len(words) - phrase_length * 2):
            phrase = " ".join(words[i:i+phrase_length]).lower()
            # Skip very short or common phrases
            if len(phrase) < 8 and not any(word in phrase.lower() for word in ['thank', 'watching', 'luck']):
                continue
                
            occurrences = 1  # Start with 1 since we're looking at the current phrase
            positions = [i]
            
            # Count occurrences and positions
            for j in range(i + phrase_length, len(words) - phrase_length + 1, 1):
                if " ".join(words[j:j+phrase_length]).lower() == phrase:
                    occurrences += 1
                    positions.append(j)
                    
            if occurrences >= 2:
                # Keep only the first occurrence
                first_pos = positions[0]
                first_phrase = " ".join(words[first_pos:first_pos+phrase_length])
                
                # Build a new text
                before_first = " ".join(words[:first_pos])
                after_last_unique = []
                last_repeated_end = positions[-1] + phrase_length
                if last_repeated_end < len(words):
                    after_last_unique = words[last_repeated_end:]
                
                new_text = before_first + " " + first_phrase
                if after_last_unique:
                    new_text += " " + " ".join(after_last_unique)
                
                return new_text.strip()
    
    # 3. Check for longer repeated sequences (4+ words)
    for phrase_length in range(4, 12):  # Check phrases of different lengths
        if len(words) < phrase_length * 2:
            continue
            
        for i in range(len(words) - phrase_length * 2):
            phrase1 = " ".join(words[i:i+phrase_length])
            occurrences = 0
            
            # Count occurrences of this phrase in the remaining text
            for j in range(i, len(words) - phrase_length + 1, phrase_length):
                if " ".join(words[j:j+phrase_length]) == phrase1:
                    occurrences += 1
                else:
                    break
                    
            # If phrase repeats 2+ times, it's likely hallucination
            if occurrences >= 2:
                # Create regex pattern to remove all but the first occurrence
                pattern = f"({re.escape(phrase1)}\\s*)+"
                clean_text = re.sub(pattern, phrase1 + " ", clean_text)
                return clean_text.strip()
    
    # 4. Check for sentences repeating at the end
    sentences = re.split(r'[.!?]+\s*', clean_text)
    if len(sentences) >= 3:
        last_sentence = sentences[-1].strip()
        second_last = sentences[-2].strip()
        
        # If last sentence and second last are the same, remove the last one
        if last_sentence and last_sentence.lower() == second_last.lower():
            clean_text = '.'.join(sentences[:-1]) + '.'
            return clean_text
    
    return clean_text

def transcribe_and_send(button_type):
    """Transcribe and send to AI model."""
    global filename, clipboard_content

    if filename is None:
        print("No recording found. Please record something first.")
        return

    start_time = time.time()
    log_memory_usage()  # Log memory before transcription

    # Define content based on button clicked
    if button_type == "record" or button_type == "select_file":
        content = (
            "I will be sending you voice messages in either English or German that require conversion into text for "
            "emails in the language of the input message. It's essential if the input is English it remains English. "
            "The same applies if the input is German, keep it German. Conduct a spell check to correct any "
            "typographical errors while preserving the exact phrasing of my messages, unless there are clear spelling "
            "mistakes. Please format these texts with appropriate line breaks to enhance readability for email "
            "communication. The responses should be crafted as if I, Andrew, am directly replying. Refrain from adding "
            "a subject line; I only need the refined, raw email text. Ensure that the wording remains mostly unchanged "
            "to retain my original message's integrity, but improve certain phrases and amend evident typos."
        )
    elif button_type == "command":
        content = (
            "You are Andrew's personal assistant. Provide extremely concise, direct answers with no extra text or explanations. "
            "For URLs, provide only the URL. For facts, provide only the answer. For questions like 'What is the capital of England?' "
            "respond only with 'London'. Be as brief as possible while being accurate."
        )
    elif button_type == "notes":
        content = "N/A"

    try:
        # Handle .aac files if needed
        if filename.lower().endswith('.aac'):
            print(f"Converting {filename} to WAV format...")
            audio = AudioSegment.from_file(filename, format='aac')
            
            # ENHANCEMENT: Increase volume for AAC files to improve transcription
            # AAC files often have lower volume when converted
            audio = audio + 20  # This increases volume by 20dB
            print("Applied +20dB amplification to audio")
            
            wav_filename = tempfile.mktemp(suffix='.wav')
            audio.export(wav_filename, format='wav')
            print(f"Conversion complete. WAV file saved at {wav_filename}")
            result = pipe(wav_filename)
        else:
            # ENHANCEMENT: Volume improvement for WAV files
            # For WAV files, check if volume enhancement is needed
            audio_data, sr = sf.read(filename)
            max_amplitude = np.max(np.abs(audio_data))
            
            # Always enhance the audio volume for better transcription
            print(f"Enhancing audio volume for better transcription (original max amplitude: {max_amplitude:.4f})")
            
            # Create a temporary file for the enhanced audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
                enhanced_filename = tf.name
            
            # Apply different gain strategies based on the original volume
            if max_amplitude < 0.1 and max_amplitude > 0:
                # Very quiet audio needs strong amplification
                gain_factor = 1.8 / max_amplitude  # Increased from 0.9
                enhanced_audio = np.clip(audio_data * gain_factor, -1.0, 1.0)  # Clip to prevent distortion
                print(f"Applied high gain factor of {gain_factor:.2f}x to very quiet audio")
            else:
                # Standard audio gets a fixed boost
                gain_factor = 2.0  # Double the volume
                enhanced_audio = np.clip(audio_data * gain_factor, -1.0, 1.0)
                print(f"Applied standard gain factor of {gain_factor:.2f}x")
            
            sf.write(enhanced_filename, enhanced_audio, sr)
            print(f"Enhanced audio saved to {enhanced_filename}")
            
            # Use the enhanced file for transcription
            print("Starting transcription with enhanced audio...")
            result = pipe(enhanced_filename)
            
            print("Transcription completed")

        text = result["text"]
        text = remove_you_thank_you(text)
        # Remove any repetitive hallucinated phrases
        text = remove_repetitive_phrases(text)
        pyperclip.copy(text)
        print(f"Transcription: {text}")

        # Send transcription to AI model
        if button_type == "command":
            ai_response = send_transcription(text, content, clipboard_content)
        else:
            ai_response = send_transcription(text, content)

        formatted_response = format_response(ai_response)
        pyperclip.copy(formatted_response)
        print(f"Formatted Response: {formatted_response}")
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        traceback.print_exc()

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    log_memory_usage()  # Log memory after transcription

def transcribe_and_paste():
    """Transcribe the audio, copy to clipboard, and simulate paste."""
    global filename
    if filename is None:
        print("No recording found. Please record something first.")
        return

    start_time = time.time()

    try:
        # Save current clipboard content before we change it
        save_clipboard_content()
        
        result = pipe(filename)
        text = result["text"]
        text = remove_you_thank_you(text)
        # Remove any repetitive hallucinated phrases
        text = remove_repetitive_phrases(text)
        set_clipboard_text(text)
        print(f"Transcription: {text}")
        # Simulate Ctrl+V to paste the transcribed text
        keyboard.press_and_release('ctrl+v')
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        traceback.print_exc()

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

# Function to get clipboard content (text or image)
def get_clipboard_content():
    """Get current clipboard content and format."""
    global win32_available
    
    if not win32_available:
        # Fallback to pyperclip for text only
        try:
            text = pyperclip.paste()
            if text:
                return text, "text"
            return None, None
        except Exception as e:
            print(f"Error getting clipboard text: {e}")
            return None, None
    
    try:
        win32clipboard.OpenClipboard()
        
        # Try to get image from clipboard
        if win32clipboard.IsClipboardFormatAvailable(CF_DIB):
            try:
                data = win32clipboard.GetClipboardData(CF_DIB)
                win32clipboard.CloseClipboard()
                return data, "image"
            except Exception as e:
                print(f"Error getting image from clipboard: {e}")
                win32clipboard.CloseClipboard()
        
        # Try to get text from clipboard
        elif win32clipboard.IsClipboardFormatAvailable(CF_UNICODETEXT):
            try:
                text = win32clipboard.GetClipboardData(CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                return text, "text"
            except Exception as e:
                print(f"Error getting text from clipboard: {e}")
                win32clipboard.CloseClipboard()
        else:
            win32clipboard.CloseClipboard()
            
        return None, None
    except Exception as e:
        print(f"Error accessing clipboard: {e}")
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        return None, None

# Function to set clipboard content
def set_clipboard_text(text):
    """Set clipboard content to text."""
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"Error setting clipboard text: {e}")
        return False

# Function to set image to clipboard
def set_clipboard_image(image_data):
    """Set clipboard content to image."""
    global win32_available
    
    if not win32_available:
        print("Cannot set image to clipboard: win32clipboard not available")
        return False
    
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(CF_DIB, image_data)
        win32clipboard.CloseClipboard()
        print("Image set to clipboard successfully")
        return True
    except Exception as e:
        print(f"Error setting clipboard image: {e}")
        traceback.print_exc()
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        return False

# Function to save current clipboard content before transcription
def save_clipboard_content():
    """Save current clipboard content before changing it."""
    global previous_clipboard, clipboard_format
    
    content, format_type = get_clipboard_content()
    if content:
        previous_clipboard = content
        clipboard_format = format_type
        if format_type == "text":
            print(f"Saved previous clipboard text: {content[:30]}{'...' if len(content) > 30 else ''}")
        else:
            print("Saved previous clipboard image")
        return True
    return False

def transcribe_and_paste_with_previous():
    """Transcribe the audio, then paste with two enters and previously copied item."""
    global filename, previous_clipboard, clipboard_format
    if filename is None:
        print("No recording found. Please record something first.")
        return

    start_time = time.time()

    try:
        # Always get the current clipboard content when the function is called
        # This ensures we always use the most recently copied item
        save_clipboard_content()
        
        if clipboard_format == "text" and previous_clipboard:
            # Handle text content
            print(f"Using previous clipboard text: {previous_clipboard[:30]}{'...' if len(previous_clipboard) > 30 else ''}")
            
            # Transcribe the audio
            result = pipe(filename)
            text = result["text"]
            text = remove_you_thank_you(text)
            
            # First paste the transcription
            print("Setting transcription to clipboard...")
            set_clipboard_text(text)
            print(f"Transcription: {text}")
            print("Pasting transcription...")
            keyboard.press_and_release('ctrl+v')
            time.sleep(0.3)
            
            # Press Shift+Enter twice for two line breaks
            print("Adding two line breaks...")
            keyboard.press_and_release('shift+enter')
            time.sleep(0.2)
            keyboard.press_and_release('shift+enter')
            time.sleep(0.2)
            
            # Now paste the previous text
            print("Setting previous text to clipboard...")
            set_clipboard_text(previous_clipboard)
            print(f"Previous clipboard (text): {previous_clipboard[:50]}{'...' if len(previous_clipboard) > 50 else ''}")
            print("Pasting previous text...")
            keyboard.press_and_release('ctrl+v')
            
            # Press Enter to complete the message
            time.sleep(0.3)
            keyboard.press_and_release('enter')
            
        elif clipboard_format == "image" and previous_clipboard and win32_available:
            # Handle image content
            print("Using previous clipboard image")
            
            # Transcribe the audio first
            result = pipe(filename)
            text = result["text"]
            text = remove_you_thank_you(text)
            print(f"Transcription: {text}")
            print("Previous clipboard: [IMAGE]")
            
            # First paste the transcription
            print("Setting text to clipboard...")
            set_clipboard_text(text)
            print("Pasting transcription...")
            keyboard.press_and_release('ctrl+v')
            time.sleep(0.3)
            
            # Press Shift+Enter twice for two line breaks
            print("Adding two line breaks...")
            keyboard.press_and_release('shift+enter')
            time.sleep(0.2)
            keyboard.press_and_release('shift+enter')
            time.sleep(0.2)
            
            # Now paste the image
            print("Setting image to clipboard...")
            success = set_clipboard_image(previous_clipboard)
            if success:
                print("Pasting image...")
                keyboard.press_and_release('ctrl+v')
                # Press Enter to complete the message
                time.sleep(0.3)
                keyboard.press_and_release('enter')
            else:
                # If image paste failed, just complete the message
                print("Image paste failed")
                keyboard.press_and_release('enter')
            
        else:
            # No previous content or unsupported format, just paste the transcription
            result = pipe(filename)
            text = result["text"]
            text = remove_you_thank_you(text)
            set_clipboard_text(text)
            print(f"Transcription: {text}")
            print("No usable previous clipboard content found")
            keyboard.press_and_release('ctrl+v')
            
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        traceback.print_exc()

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

def create_notes_from_transcription():
    """Generate bullet-point notes from transcription."""
    global filename
    if not filename:
        print("No recording found. Please record something first.")
        return
    result = pipe(filename)
    text = remove_you_thank_you(result["text"])
    # Remove any repetitive hallucinated phrases
    text = remove_repetitive_phrases(text)
    bullets = "\n".join([f"- {line.strip()}" for line in text.split('.') if line.strip()])
    pyperclip.copy(bullets)
    print(f"Notes:\n{bullets}")

def command_button_clicked():
    toggle_recording("command")

def notes_button_clicked():
    toggle_recording("notes")

def ctrl_alt_a_callback():
    # Ctrl+Alt+A triggers normal record/transcribe with email formatting
    toggle_recording("record")

def ctrl_alt_x_callback():
    # Ctrl+Alt+X triggers transcribe and paste (as per old functionality)
    toggle_recording("transcribe_paste")
    
def ctrl_alt_f_callback():
    # Ctrl+Alt+F triggers transcribe and paste with previous clipboard content
    # Clear any previous clipboard content to ensure we get the most recent
    global previous_clipboard, clipboard_format
    previous_clipboard = None
    clipboard_format = None
    toggle_recording("transcribe_paste_with_previous")

def select_audio_file():
    """Open a file dialog to select an audio file and process it."""
    global filename, last_button_clicked
    filetypes = [('AAC files', '*.aac'), ('All files', '*.*')]
    filename = filedialog.askopenfilename(title='Open an audio file', filetypes=filetypes)
    if filename:
        print(f"Selected file: {filename}")
        last_button_clicked = 'select_file'
        handle_transcription()

def email_button_clicked():
    """Handle email button click."""
    toggle_recording("email")

def transcribe_and_send_email():
    """Transcribe and send email with Alt+H shortcut."""
    global filename
    if filename is None:
        print("No recording found. Please record something first.")
        return

    try:
        result = pipe(filename)
        text = result["text"]
        text = remove_you_thank_you(text)
        
        # Add the requested prefix to the email text
        formatted_email = "Form this message as a email. Correct obvious typos and fill in obvious blanks. Keep the same wording as much as possible. Here is the message: " + text
        
        pyperclip.copy(formatted_email)
        print(f"Original transcription: {text}")
        print(f"Formatted as email with instructions")
        
        # Simulate Alt+H and Enter
        keyboard.press_and_release('alt+h')
        time.sleep(0.5)  # Small delay to ensure the shortcut is registered
        keyboard.write(formatted_email)
        keyboard.press_and_release('enter')
        
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        traceback.print_exc()

# Function to create circular icon buttons
def create_circular_icon(color, size=40, icon_text=""):
    # Create a circular image
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw circle
    draw.ellipse((0, 0, size-1, size-1), fill=color)
    
    # Add text if provided
    if icon_text:
            # For simplicity, we're using text instead of proper icons
            # In a production app, you'd load actual icon images
            draw.text((size//2, size//2), icon_text, fill="white", anchor="mm")
        
    return ImageTk.PhotoImage(image)

# Create frame for icons
icon_frame = tk.Frame(root, bg="#1a2b47")
icon_frame.pack(fill=tk.BOTH, expand=True)

# Icon data with colors, symbols, and functions
icons_data = [
    {"color": "#000000", "text": "🎤", "tooltip": "Ctrl+Alt+X", "command": ctrl_alt_x_callback},
    {"color": "#4285F4", "text": "🔊", "tooltip": "Ctrl+Alt+Y", "command": lambda: toggle_recording("email")},
    {"color": "#EA4335", "text": "⏺", "tooltip": "Record", "command": lambda: toggle_recording("record")},
    {"color": "#34A853", "text": "💬", "tooltip": "Command", "command": command_button_clicked},
    {"color": "#FBBC05", "text": "📂", "tooltip": "Select File", "command": select_audio_file},
    {"color": "#9C27B0", "text": "📋", "tooltip": "Ctrl+Alt+F", "command": ctrl_alt_f_callback}
]

# Store button references
buttons = []
button_images = []

# Create the buttons
for i, icon_data in enumerate(icons_data):
    # Create button frame for better spacing
    btn_frame = tk.Frame(icon_frame, bg="#1a2b47", padx=5)
    btn_frame.pack(side=tk.LEFT)
    
    # Create the icon image
    icon_img = create_circular_icon(icon_data["color"], 40, icon_data["text"])
    button_images.append(icon_img)  # Keep reference to prevent garbage collection
    
    # Create the button
    btn = tk.Button(
        btn_frame, 
        image=icon_img, 
        bg="#1a2b47", 
        activebackground="#1a2b47",
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        command=icon_data["command"]
    )
    btn.image = icon_img  # Keep a reference
    btn.pack(pady=2)
    
    # Add tooltip if specified
    if "tooltip" in icon_data:
        tooltip = tk.Label(
            btn_frame, 
            text=icon_data["tooltip"],
            bg="#1a2b47",
            fg="white",
            font=("Arial", 7)
        )
        tooltip.pack()
    
    # Add hover effect
    btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#2a3b57"))
    btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#1a2b47"))
    
    buttons.append(btn)

# Map the buttons to variables for function access
button = buttons[2]  # Record button
command_button = buttons[3]  # Command button
notes_button = None  # Notes functionality is now in buttons[0] (ctrl+alt+x)
select_button = buttons[4]  # Select Audio File button
email_button = buttons[1]  # Email button
previous_paste_button = buttons[5]  # Previous paste button (Ctrl+Alt+F)

# Add this function to check if hotkeys are working
def register_hotkeys():
    try:
        print("Registering hotkeys...")
        keyboard.add_hotkey('ctrl+alt+a', ctrl_alt_a_callback)
        print("Registered Ctrl+Alt+A")
        
        keyboard.add_hotkey('ctrl+alt+x', ctrl_alt_x_callback)
        print("Registered Ctrl+Alt+X")
        
        keyboard.add_hotkey('ctrl+alt+y', lambda: toggle_recording("email"))
        print("Registered Ctrl+Alt+Y")
        
        keyboard.add_hotkey('ctrl+alt+f', ctrl_alt_f_callback)
        print("Registered Ctrl+Alt+F")
        
        print("All hotkeys registered successfully")
    except Exception as e:
        print(f"Error registering hotkeys: {e}")
        traceback.print_exc()

# Create a separate thread for hotkey registration
def start_hotkey_thread():
    try:
        # Run the register_hotkeys function directly in the main thread
        # This ensures all hotkeys are registered before the main loop starts
        register_hotkeys()
        return None  # No thread created, function executed directly
    except Exception as e:
        print(f"Error in hotkey registration: {e}")
        traceback.print_exc()
        return None

# Register hotkeys directly instead of in a separate thread
# This avoids potential race conditions and ensures all hotkeys are registered
start_hotkey_thread()

# Add webrtcvad to requirements if not already installed
print("\nNOTE: This script requires the webrtcvad package for voice activity detection.")
print("If not installed, run: pip install webrtcvad")

# We don't need a periodic clipboard check anymore
# Instead, we'll capture the clipboard content right before we need it
# This is more efficient and avoids potential threading issues

# Display info about variable-length recording
print("\nVariable-length recording enabled:")
print(f"- Maximum duration: {max_duration} seconds")
print(f"- Will stop automatically after {silence_duration} seconds of silence")
print(f"- Voice activity detection: {'Enabled' if vad_available else 'Using amplitude fallback'}")

root.mainloop()
