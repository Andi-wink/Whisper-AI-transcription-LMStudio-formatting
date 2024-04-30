import tkinter as tk
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import time
import pyperclip  # Make sure to install this with pip install pyperclip
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
# from Local_AI_server import send_transcription
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

with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
    filename = tf.name
    print(f"Audio file saved at: {filename}")

def toggle_recording():
    global is_recording, recording, filename

    if not is_recording:
        # Start recording
        is_recording = True
        button.config(text="Stop Recording")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
            filename = tf.name
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        # Removed messagebox.showinfo for starting recording
    else:
        # Stop recording
        is_recording = False
        button.config(text="Record", state="normal")
        sd.stop()
        sf.write(filename, recording, sample_rate)
        transcribe()


def transcribe():
    # Start the timer
    start_time = time.time()

    # Transcribe the audio file
    result = pipe(filename)

    # End the timer
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time

    text = result["text"]
    pyperclip.copy(text)  # Copy the transcription text to the clipboard
    print(f"Transcription: {text}\n\nTime taken: {elapsed_time:.2f} seconds")
    # Removed messagebox.showinfo for transcription


button = tk.Button(root, text="Record", font=("Arial", 14), command=toggle_recording)
button.pack(padx=20, pady=20)

# Bind the Ctrl + t hotkey to the toggle recording function
root.bind('<Control-t>', lambda event: toggle_recording())

root.mainloop()

