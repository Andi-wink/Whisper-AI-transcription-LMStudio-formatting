import tkinter as tk
from tkinter import filedialog
import threading
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import time
import pyperclip
import re
import traceback
from pydub import AudioSegment
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline, GenerationConfig
import keyboard
from Local_AI_server import send_transcription  # Import the server-side function

# Set device to GPU if available
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Load the model
model_id = "openai/whisper-large-v2"  # Ensure you have a valid model ID
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True
)
model.to(device)

# Initialize the generation config
model.generation_config = GenerationConfig.from_pretrained(model_id)

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

# Initialize recording state and other variables
is_recording = False
is_transcribing = False
recording = None
filename = None
duration = 90  # seconds (adjust as needed)
sample_rate = 44100
last_button_clicked = None
clipboard_content = None

# Initialize the main Tkinter window
root = tk.Tk()
root.geometry("600x700")
root.title("Speech Recorder")
root.configure(background="#4a4a4a")

label = tk.Label(root, text="Speech Recorder", font=("Arial", 18))
label.pack(padx=20, pady=20)

def select_audio_file():
    """Open a file dialog to select an audio file and process it."""
    global filename, last_button_clicked
    # Open file dialog to select .aac files
    filetypes = [('AAC files', '*.aac'), ('All files', '*.*')]
    filename = filedialog.askopenfilename(title='Open an audio file', filetypes=filetypes)
    if filename:
        print(f"Selected file: {filename}")
        last_button_clicked = 'select_file'  # Set the last button clicked
        handle_transcription()  # Process the selected file

def handle_transcription():
    """Handle the transcription after recording is stopped or file is selected."""
    global is_transcribing, last_button_clicked
    if not is_transcribing:
        is_transcribing = True
        # Start a new thread for transcription
        transcription_thread = threading.Thread(target=transcription_worker)
        transcription_thread.start()

def transcription_worker():
    """Worker function to perform transcription in a separate thread."""
    global is_transcribing, last_button_clicked
    try:
        if last_button_clicked == "command":
            transcribe_and_send("command")
        elif last_button_clicked == "spaceholder":
            transcribe_and_send("spaceholder")
        elif last_button_clicked == "record":
            transcribe_and_send("record")
        elif last_button_clicked == "transcribe_paste":
            transcribe_and_paste()
        elif last_button_clicked == "select_file":
            transcribe_and_send("select_file")
    except Exception as e:
        print(f"An error occurred in transcription_worker: {e}")
        traceback.print_exc()
    finally:
        is_transcribing = False

def remove_you_thank_you(text):
    """Remove any trailing 'you' or 'thank you' from the end of the text."""
    pattern = r'(?:\s*(?:you|thank you)[\s\.,;!\?]*)+$'
    text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
    return text

def transcribe_and_send(button_type):
    """Transcribe the audio file and send the transcription to the AI model."""
    global filename, clipboard_content

    if filename is None:
        print("No recording found or file selected. Please provide an audio file first.")
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
            "to retain my original message's integrity, but improve certain phrases and amend evident typos. Do not "
            "add: Here is the converted text: at the beginning of your reply. If there is 'you' or 'thank you' at the "
            "end of the transcription remove it."
        )
    elif button_type == "command":
        content = (
            "You are Andrew's assistant. Listen to his instructions and respond to messages sent to him as he would "
            "in a professional way and format your response as if it were a business email."
        )
    elif button_type == "spaceholder":
        content = "This is the spaceholder button content."
    elif button_type == "select_file":
        # Use the same content as 'record' or customize as needed
        content = (
            "I will be sending you voice messages in either English or German that require conversion into text for "
            "emails in the language of the input message. It's essential if the input is English it remains English. "
            "The same applies if the input is German, keep it German. Conduct a spell check to correct any "
            "typographical errors while preserving the exact phrasing of my messages, unless there are clear spelling "
            "mistakes. Please format these texts with appropriate line breaks to enhance readability for email "
            "communication. The responses should be crafted as if I, Andrew, am directly replying. Refrain from adding "
            "a subject line; I only need the refined, raw email text. Ensure that the wording remains mostly unchanged "
            "to retain my original message's integrity, but improve certain phrases and amend evident typos. Do not "
            "add: Here is the converted text: at the beginning of your reply. If there is 'you' or 'thank you' at the "
            "end of the transcription remove it."
        )

    try:
        # Convert .aac file to .wav using pydub
        print(f"Converting {filename} to WAV format...")
        audio = AudioSegment.from_file(filename, format='aac')
        wav_filename = tempfile.mktemp(suffix='.wav')
        audio.export(wav_filename, format='wav')
        print(f"Conversion complete. WAV file saved at {wav_filename}")

        # Transcribe the audio file using the pipeline directly
        print(f"Starting transcription of {wav_filename}...")
        result = pipe(wav_filename)
        print("Transcription complete.")
        text = result["text"]

        # Remove 'you' and 'thank you' at the end
        text = remove_you_thank_you(text)

        pyperclip.copy(text)  # Copy the transcription text to the clipboard
        print(f"Transcription: {text}")

        # Send transcription and additional content to the AI model and get response
        print("Sending transcription to AI model...")
        if button_type == "command":
            ai_response = send_transcription(text, content, clipboard_content)
        else:
            ai_response = send_transcription(text, content)
        print("Received response from AI model.")

        formatted_response = format_response(ai_response)
        pyperclip.copy(formatted_response)
        print(f"Formatted Response: {formatted_response}")

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        traceback.print_exc()
    finally:
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.2f} seconds")

def transcribe_and_paste():
    """Transcribe the audio file, process the text, copy to clipboard, and simulate paste."""
    global filename

    if filename is None:
        print("No recording found or file selected. Please provide an audio file first.")
        return

    start_time = time.time()

    try:
        # Convert .aac file to .wav using pydub
        print(f"Converting {filename} to WAV format...")
        audio = AudioSegment.from_file(filename, format='aac')
        wav_filename = tempfile.mktemp(suffix='.wav')
        audio.export(wav_filename, format='wav')
        print(f"Conversion complete. WAV file saved at {wav_filename}")

        # Transcribe the audio file using the pipeline directly
        print(f"Starting transcription of {wav_filename}...")
        result = pipe(wav_filename)
        print("Transcription complete.")
        text = result["text"]

        # Process the text to remove trailing 'you' or 'thank you'
        text = remove_you_thank_you(text)

        # Copy the processed transcription text to the clipboard
        pyperclip.copy(text)
        print(f"Transcription: {text}")

        # Simulate a 'ctrl+v' keypress to paste the text
        keyboard.press_and_release('ctrl+v')

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        traceback.print_exc()
    finally:
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.2f} seconds")

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

def update_button_text(button_type):
    """Update the button text based on the current state."""
    global is_recording

    if button_type == "record":
        button.config(text="Stop Recording" if is_recording else "Record")
    elif button_type == "command":
        command_button.config(text="Stop Command Recording" if is_recording else "Command")
    elif button_type == "spaceholder":
        spaceholder_button.config(text="Stop Spaceholder Recording" if is_recording else "Spaceholder")
    elif button_type == "transcribe_paste":
        pass  # No button to update

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

def ctrl_alt_x_callback():
    """Handle Ctrl + Alt + X hotkey event."""
    print("Global hotkey Ctrl + Alt + X triggered")
    toggle_recording("transcribe_paste")

# Create GUI buttons
select_button = tk.Button(root, text="Select Audio File", font=("Arial", 14), command=select_audio_file)
select_button.pack(padx=20, pady=20)

button = tk.Button(root, text="Record", font=("Arial", 14), command=lambda: toggle_recording("record"))
button.pack(padx=20, pady=20)

command_button = tk.Button(root, text="Command", font=("Arial", 14), command=command_button_clicked)
command_button.pack(padx=20, pady=20)

spaceholder_button = tk.Button(root, text="Spaceholder", font=("Arial", 14), command=spaceholder_button_clicked)
spaceholder_button.pack(padx=20, pady=20)

# Bind the global hotkeys
keyboard.add_hotkey('ctrl+alt+a', ctrl_alt_a_callback)
keyboard.add_hotkey('ctrl+alt+y', command_button_clicked_hotkey)
keyboard.add_hotkey('ctrl+alt+x', ctrl_alt_x_callback)

# Start the Tkinter event loop
root.mainloop()
