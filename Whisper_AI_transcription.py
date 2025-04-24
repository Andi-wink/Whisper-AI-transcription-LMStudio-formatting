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

root = tk.Tk()
root.geometry("600x700")
root.title("Speech Recorder")
root.configure(background="#4a4a4a")

label = tk.Label(root, text="Speech Recorder", font=("Arial", 18))
label.pack(padx=20, pady=20)

# Initialize states
is_recording = False
is_transcribing = False
recording = None
filename = None
duration = 90  # seconds (adjust as needed)
sample_rate = 44100
last_button_clicked = None
clipboard_content = None

def start_recording():
    """Start recording."""
    global recording, filename, is_recording
    if is_recording:
        return  # Already recording
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
        filename = tf.name
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    is_recording = True
    print("Recording started...")
    root.after(duration * 1000, stop_recording)  # Stop after set duration

def stop_recording():
    """Stop recording."""
    global recording, filename, is_recording
    if not is_recording:
        return
    sd.stop()
    
    # ENHANCEMENT: Audio volume normalization and amplification to improve transcription accuracy
    # This addresses the issue of recordings being too quiet for effective transcription
    if recording is not None and len(recording) > 0:
        # Convert to float32 if not already
        if recording.dtype != np.float32:
            recording = recording.astype(np.float32)
            
        # Calculate the maximum absolute amplitude
        max_amplitude = np.max(np.abs(recording))
        if max_amplitude > 0:
            # Check if audio is too quiet (adjust threshold as needed)
            if max_amplitude < 0.2:  # Increased threshold to catch more recordings
                print(f"Audio volume is low (max amplitude: {max_amplitude:.4f}), applying amplification")
                
                # Apply stronger normalization for better volume
                gain_factor = 1.8 / max_amplitude  # Doubled from 0.9 to 1.8 (can go to max 2.0 safely)
                recording = recording * gain_factor
                
                print(f"Applied gain factor of {gain_factor:.2f}x")
            else:
                # Even if volume is adequate, still boost it a bit
                gain_factor = 2.0  # Fixed gain for all recordings
                recording = np.clip(recording * gain_factor, -1.0, 1.0)  # Clip to prevent distortion
                print(f"Applied standard boost of {gain_factor:.2f}x to all audio")
        else:
            print("Warning: Recording appears to be silent (max amplitude: 0)")
    
    sf.write(filename, recording, sample_rate)
    is_recording = False
    print(f"Recording saved to {filename}")
    handle_transcription()

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
            "You are Andrew's assistant. Listen to his instructions and respond to messages sent to him as he would "
            "in a professional way and format your response as if it were a business email."
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
        result = pipe(filename)
        text = result["text"]
        text = remove_you_thank_you(text)
        pyperclip.copy(text)
        print(f"Transcription: {text}")
        # Simulate Ctrl+V to paste the transcribed text
        keyboard.press_and_release('ctrl+v')
    except Exception as e:
        print(f"An error occurred during transcription: {e}")

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
        pyperclip.copy(text)
        print(f"Transcription: {text}")
        
        # Simulate Alt+H and Enter
        keyboard.press_and_release('alt+h')
        time.sleep(0.5)  # Small delay to ensure the shortcut is registered
        keyboard.write(text)
        keyboard.press_and_release('enter')
        
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        traceback.print_exc()

button = tk.Button(root, text="Record", font=("Arial", 14), command=lambda: toggle_recording("record"))
button.pack(padx=20, pady=20)

command_button = tk.Button(root, text="Command", font=("Arial", 14), command=command_button_clicked)
command_button.pack(padx=20, pady=20)

notes_button = tk.Button(root, text="Notes", font=("Arial", 14), command=notes_button_clicked)
notes_button.pack(padx=20, pady=20)

select_button = tk.Button(root, text="Select Audio File", font=("Arial", 14), command=select_audio_file)
select_button.pack(padx=20, pady=20)

email_button = tk.Button(root, text="Email", font=("Arial", 14), command=email_button_clicked)
email_button.pack(padx=20, pady=20)

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
        
        print("All hotkeys registered successfully")
    except Exception as e:
        print(f"Error registering hotkeys: {e}")
        traceback.print_exc()

# Create a separate thread for hotkey registration
def start_hotkey_thread():
    hotkey_thread = threading.Thread(target=register_hotkeys)
    hotkey_thread.daemon = True
    hotkey_thread.start()
    return hotkey_thread

# Replace the direct hotkey registration with the threaded version
hotkey_thread = start_hotkey_thread()

root.mainloop()
