import tkinter as tk
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import time
import pyperclip  # Make sure to install this with pip install pyperclip
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
# Ensure the chat_interaction.py is accessible or the send_transcription function is defined/imported here
from Local_AI_server import send_transcription
import keyboard

# Set device to GPU if available
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Load the model
model_id = "openai/whisper-large-v3"
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)

# Load the processor
processor = AutoProcessor.from_pretrained(model_id)

# Initialize the pipeline
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

root = tk.Tk()
root.geometry("600x500")
root.title("Speech Recorder")
root.configure(background="#4a4a4a")

label = tk.Label(root, text="Speech Recorder", font=("Arial", 18))
label.pack(padx=20, pady=20)

# Initialize recording state
is_recording = False
recording = None
filename = None
duration = 60  # seconds
sample_rate = 44100

def toggle_recording():
    global is_recording, recording, filename

    if not is_recording:
        # Start recording
        is_recording = True
        button.config(text="Stop Recording")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
            filename = tf.name
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    else:
        # Stop recording
        is_recording = False
        button.config(text="Record", state="normal")
        sd.stop()
        sf.write(filename, recording, sample_rate)
        transcribe_and_send()

def transcribe_and_send():
    start_time = time.time()

    # Transcribe the audio file
    result = pipe(filename)
    text = result["text"]
    pyperclip.copy(text)  # Copy the transcription text to the clipboard
    print(f"Transcription: {text}")

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    # Send transcription to the AI model
    send_transcription(text)  # Default to email instructions

def command_button_clicked():
    start_time = time.time()

    # Transcribe the audio file
    result = pipe(filename)
    text = result["text"]
    pyperclip.copy(text)  # Copy the transcription text to the clipboard
    print(f"Transcription: {text}")

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    # Send transcription to the AI model with command instructions
    send_transcription(text)

def ctrl_alt_a_callback():
    toggle_recording()

button = tk.Button(root, text="Record", font=("Arial", 14), command=toggle_recording)
button.pack(padx=20, pady=20)

command_button = tk.Button(root, text="Command", font=("Arial", 14), command=command_button_clicked)
command_button.pack(padx=20, pady=20)

spaceholder_button = tk.Button(root, text="Spaceholder", font=("Arial", 14))
spaceholder_button.pack(padx=20, pady=20)

# Bind the Ctrl + Alt + A hotkey to the toggle recording function
keyboard.add_hotkey('ctrl+alt+a', ctrl_alt_a_callback)

root.mainloop()