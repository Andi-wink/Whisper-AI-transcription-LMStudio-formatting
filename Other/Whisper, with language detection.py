import cProfile
import tkinter as tk
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import time
import pyperclip
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

def main():
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
    transcribe_in_german = False

    def toggle_recording(german=False):
        nonlocal is_recording, recording, filename, transcribe_in_german
        transcribe_in_german = german

        if not is_recording:
            # Start recording
            is_recording = True
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
            button.config(text="Stop Transcription" if not german else "Stop German Transcription")
            german_button.config(text="Stop Transcription" if german else "Stop German Transcription")
        else:
            # Stop recording and start transcribing
            is_recording = False
            sd.wait()  # Wait for the recording to finish
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
                filename = tf.name
                sf.write(filename, recording, sample_rate)
            print(f"Audio file saved at: {filename}")
            transcribe()
            button.config(text="Transcribe")
            german_button.config(text="Transcribe in German")

    def transcribe():
        nonlocal filename, transcribe_in_german
        if filename is not None:
            start_time = time.time()
            kwargs = {"language": "de"} if transcribe_in_german else {}
            result = pipe(filename, generate_kwargs=kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            text = result["text"]
            pyperclip.copy(text)
            print(f"Transcription: {text}\n\nTime taken: {elapsed_time:.2f} seconds")
        else:
            print("No recording available to transcribe.")

    def hotkey_transcribe_default(event=None):
        toggle_recording(german=False)

    def hotkey_transcribe_german(event=None):
        toggle_recording(german=True)

    button = tk.Button(root, text="Transcribe", font=("Arial", 14), command=hotkey_transcribe_default)
    button.pack(padx=20, pady=20)

    german_button = tk.Button(root, text="Transcribe in German", font=("Arial", 14), command=hotkey_transcribe_german)
    german_button.pack(padx=20, pady=20)

    root.bind('<Control-t>', hotkey_transcribe_default)
    root.bind('<Control-d>', hotkey_transcribe_german)

    root.mainloop()

if __name__ == "__main__":
    profile_filename = 'profiling_data.prof'
    cProfile.run('main()', profile_filename)

    # To visualize the profiling data, run this in the terminal:
    # snakeviz profiling_data.prof
