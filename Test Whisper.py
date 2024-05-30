import tkinter as tk
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import time
import pyperclip
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import keyboard
from Local_AI_server import send_transcription  # Import the server-side function

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
    """Toggle recording state."""
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
        transcribe_and_send("record")

def transcribe_and_send(button_type):
    """Transcribe the audio file and send the transcription to the AI model."""
    start_time = time.time()

    # Define the content based on button clicked
    if button_type == "record":
        content = ", unless there are clear spelling mistakes. Please format these texts with appropriate line breaks to enhance readability for email communication. The responses should be crafted as if I, Andrew, am directly replying. Refrain from adding a subject line; I only need the refined, raw email text. Ensure that the wording remains mostly unchanged to retain my original message's integrity, but improve certain phrases and ammend evident typos. Don't not add: Here is the converted text: at the beginning of your reply. If there is you you or you at the the end of the transcription remove it"
    elif button_type == "command":
        content = "make a bullet point summary of what I'm transcribing to you. Add bullet point symbols, make line breaks between each point made, keep the original wording of the transcription"
    elif button_type == "spaceholder":
        content = "I will be sending you voice messages in either English or German that require conversion into text for emails in the language of the input message. It's essential if the input is English it remains English. The same applies if the input is German, keep it German. Conduct a spell check to correct any typographical errors while preserving the exact phrasing of my messages, unless there are clear spelling mistakes. If there is you you or you at the the end of the transcription remove it"

    # Transcribe the audio file
    result = pipe(filename)
    text = result["text"]
    pyperclip.copy(text)  # Copy the transcription text to the clipboard
    print(f"Transcription: {text}")

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    # Send transcription to the AI model and get response
    ai_response = send_transcription(text, content)  # Pass the content based on button clicked
    formatted_response = format_response(ai_response)
    pyperclip.copy(formatted_response)
    print(f"Formatted Response: {formatted_response}")

def command_button_clicked():
    """Handle the command button click event."""
    transcribe_and_send("command")

def spaceholder_button_clicked():
    """Handle the spaceholder button click event."""
    transcribe_and_send("spaceholder")

def format_response(response):
    """Format the AI response by removing unwanted phrases and ensuring proper formatting."""
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

def ctrl_alt_a_callback():
    """Handle Ctrl + Alt + A hotkey event."""
    toggle_recording()

button = tk.Button(root, text="Record", font=("Arial", 14), command=toggle_recording)
button.pack(padx=20, pady=20)

command_button = tk.Button(root, text="Command", font=("Arial", 14), command=command_button_clicked)
command_button.pack(padx=20, pady=20)

spaceholder_button = tk.Button(root, text="Spaceholder", font=("Arial", 14), command=spaceholder_button_clicked)
spaceholder_button.pack(padx=20, pady=20)

# Bind the Ctrl + Alt + A hotkey to the toggle recording function
keyboard.add_hotkey('ctrl+alt+a', ctrl_alt_a_callback)

root.mainloop()
