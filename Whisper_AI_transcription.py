import tkinter as tk
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import time
import pyperclip
import re  # Import the re module for regular expressions
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
root.geometry("600x700")
root.title("Speech Recorder")
root.configure(background="#4a4a4a")

label = tk.Label(root, text="Speech Recorder", font=("Arial", 18))
label.pack(padx=20, pady=20)

# Initialize recording state
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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
        filename = tf.name
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    is_recording = True
    print("Recording started...")
    root.after(duration * 1000, stop_recording)  # Stop recording after the specified duration

def stop_recording():
    """Stop recording."""
    global recording, filename, is_recording
    if is_recording:
        sd.stop()
        sf.write(filename, recording, sample_rate)
        is_recording = False
        print(f"Recording saved to {filename}")
        handle_transcription()

def handle_transcription():
    """Handle the transcription after recording is stopped."""
    global is_transcribing
    if not is_transcribing:
        is_transcribing = True
        if last_button_clicked == "command":
            transcribe_and_send("command")
        elif last_button_clicked == "spaceholder":
            transcribe_and_send("spaceholder")
        elif last_button_clicked == "record":
            transcribe_and_send("record")
        is_transcribing = False

def toggle_recording(button_type):
    """Toggle recording state."""
    global is_recording, recording, filename, last_button_clicked, clipboard_content

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
    """Update the button text based on the current state."""
    global is_recording

    if button_type == "record":
        button.config(text="Stop Recording" if is_recording else "Record")
    elif button_type == "command":
        command_button.config(text="Stop Command Recording" if is_recording else "Command")
    elif button_type == "spaceholder":
        spaceholder_button.config(text="Stop Spaceholder Recording" if is_recording else "Spaceholder")

def remove_you_thank_you(text):
    """Remove any trailing 'you' or 'thank you' from the end of the text."""
    pattern = r'(?:\s*(?:you|thank you)[\s\.,;!\?]*)+$'
    text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
    return text

def transcribe_and_send(button_type):
    """Transcribe the audio file and send the transcription to the AI model."""
    global filename, clipboard_content

    if filename is None:
        print("No recording found. Please record something first.")
        return

    start_time = time.time()

    # Define the content based on button clicked
    if button_type == "record":
        content = (
            "I will be sending you voice messages in either English or German that require conversion into text for "
            "emails in the language of the input message. It's essential if the input is English it remains English. "
            "The same applies if the input is German, keep it German. Conduct a spell check to correct any "
            "typographical errors while preserving the exact phrasing of my messages, unless there are clear spelling "
            "mistakes. Please format these texts with appropriate line breaks to enhance readability for email "
            "communication. The responses should be crafted as if I, Andrew, am directly replying. Refrain from adding "
            "a subject line; I only need the refined, raw email text. Ensure that the wording remains mostly unchanged "
            "to retain my original message's integrity, but improve certain phrases and amend evident typos. Don't not "
            "add: Here is the converted text: at the beginning of your reply. If there is you you or you at the the "
            "end of the transcription remove it"
        )
    elif button_type == "command":
        content = (
            "You are Andrew's assistant. Listen to his instructions and respond to messages sent to him as he would "
            "in a professional way and format your response as if it were a business email."
        )
    elif button_type == "spaceholder":
        content = "This is the spaceholder button content."

    try:
        # Transcribe the audio file
        result = pipe(filename)
        text = result["text"]

        # Remove 'you' and 'thank you' at the end
        text = remove_you_thank_you(text)

        pyperclip.copy(text)  # Copy the transcription text to the clipboard
        print(f"Transcription: {text}")

        # Send transcription and additional content to the AI model and get response
        if button_type == "command":
            ai_response = send_transcription(text, content, clipboard_content)
        else:
            ai_response = send_transcription(text, content)

        formatted_response = format_response(ai_response)
        pyperclip.copy(formatted_response)
        print(f"Formatted Response: {formatted_response}")

    except Exception as e:
        print(f"An error occurred during transcription: {e}")

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

def command_button_clicked():
    """Handle the command button click event."""
    toggle_recording("command")

def command_button_clicked_hotkey():
    """Handle the command button hotkey event."""
    print("Global hotkey Ctrl + Alt + Y triggered")
    toggle_recording("command")

def spaceholder_button_clicked():
    """Handle the spaceholder button click event."""
    toggle_recording("spaceholder")

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
    print("Global hotkey Ctrl + Alt + A triggered")
    toggle_recording("record")

button = tk.Button(root, text="Record", font=("Arial", 14), command=lambda: toggle_recording("record"))
button.pack(padx=20, pady=20)

command_button = tk.Button(root, text="Command", font=("Arial", 14), command=command_button_clicked)
command_button.pack(padx=20, pady=20)

spaceholder_button = tk.Button(root, text="Spaceholder", font=("Arial", 14), command=spaceholder_button_clicked)
spaceholder_button.pack(padx=20, pady=20)

# Bind the global hotkeys
keyboard.add_hotkey('ctrl+alt+a', ctrl_alt_a_callback)
keyboard.add_hotkey('ctrl+alt+y', command_button_clicked_hotkey)

root.mainloop()
