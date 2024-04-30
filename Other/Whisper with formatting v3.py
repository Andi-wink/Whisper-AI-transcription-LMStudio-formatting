import tkinter as tk
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import time
import pyperclip
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import keyboard
import re

# Set device to GPU if available, else CPU
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Load the model and processor
model_id = "openai/whisper-large-v3"
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
).to(device)
processor = AutoProcessor.from_pretrained(model_id)

# Initialize the ASR pipeline
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=512,
    chunk_length_s=30,
    batch_size=32,
    return_timestamps=True,
    torch_dtype=torch_dtype,
    device=device,
)

# GUI setup
root = tk.Tk()
root.geometry("600x500")
root.title("Speech Recorder")
root.configure(background="#4a4a4a")

label = tk.Label(root, text="Speech Recorder", font=("Arial", 18))
label.pack(padx=20, pady=20)

# Global variables for recording
is_recording = False
recording = None
duration = 60  # seconds
sample_rate = 44100

def toggle_recording():
    global is_recording, recording, filename
    if not is_recording:
        is_recording = True
        button.config(text="Stop Recording")
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        # Create a temporary file here for consistency
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
            filename = tf.name
    else:
        is_recording = False
        button.config(text="Record", state="normal")
        sd.stop()
        # Write to the file after recording stops
        sf.write(filename, recording, sample_rate)
        transcribe()

def format_transcription(text):
    salutations = ['Hi', "Hi,", "Hallo,", "Hello", "hello", 'Hallo', 'Hello', 'Servus']
    sign_offs = ['Kind regards', 'Freundliche Grüße', 'Best regards', 'Regards']
    unwanted_endings = r'\s+you(\s+you)?\s*$'
    salutation_pattern = r'(?i)\b(' + '|'.join(salutations) + r')\s+[A-Za-z]+'
    sign_off_pattern = r'(?i)(' + '|'.join(sign_offs) + r')'
    text = re.sub(salutation_pattern, r'\g<0>,\n\n\n', text)
    text = re.sub(sign_off_pattern, r'\n\n\g<0>,\n', text)
    text = re.sub(unwanted_endings, '', text)
    return text

def transcribe():
    result = pipe(filename)
    formatted_text = format_transcription(result["text"])
    pyperclip.copy(formatted_text)
    print(f"Transcription: {formatted_text}")

button = tk.Button(root, text="Record", font=("Arial", 14), command=toggle_recording)
button.pack(padx=20, pady=20)

def toggle_recording_by_hotkey():
    root.after(0, toggle_recording)

keyboard.add_hotkey('ctrl+q', toggle_recording_by_hotkey)

root.mainloop()
