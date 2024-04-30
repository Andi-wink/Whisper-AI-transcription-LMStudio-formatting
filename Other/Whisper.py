""""

import whisper
# rest of your code

model = whisper.load_model("medium")
result = model.transcribe("Recording (2).m4a")
print(result["text"])


import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.geometry("600x500")
root.title("Speech Recorder")
root.configure(background="#4a4a4a")

label = tk.Label(root, text="Speech Recorder", font=("Arial", 18))
label.pack(padx=20, pady=20)

# How to add a textbox
textbox = tk.Text(root, font=("Arial", 14))
textbox.pack()

# this is how to add a column with buttons in it
buttonframe = tk.Frame(root)
buttonframe.columnconfigure(0, weight=1)
buttonframe.columnconfigure(1, weight=1)
buttonframe.columnconfigure(2, weight=1)

btn1 = tk.Button(buttonframe, text="1", font=("Arial", 18))
btn1.grid(row=0, column=0, sticky=tk.W + tk.E)

btn2 = tk.Button(buttonframe, text="2", font=("Arial", 18))
btn2.grid(row=0, column=1, sticky=tk.W + tk.E)

btn3 = tk.Button(buttonframe, text="3", font=("Arial", 18))
btn3.grid(row=0, column=2, sticky=tk.W + tk.E)

btn4 = tk.Button(buttonframe, text="4", font=("Arial", 18))
btn4.grid(row=1, column=0, sticky=tk.W + tk.E)

btn5 = tk.Button(buttonframe, text="5", font=("Arial", 18))
btn5.grid(row=1, column=1, sticky=tk.W + tk.E)

buttonframe.pack(fill="x")

button = tk.Button(root, text="Click to record", font=("Arial", 14))
button.pack(padx=20, pady=20)

# this is the place function, allowing you to place objects, where you want
anotherbtn = tk.Button(root, text="Test")
anotherbtn.place(x=200, y=200, height=100, width=100)

root.mainloop()
"""

import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import soundfile as sf
import tempfile
import whisper
import pyperclip

root=tk.Tk()
root.geometry("600x500")
root.title("Speech Recorder")
root.configure(background="#4a4a4a")

label = tk.Label(root, text="Speech Recorder", font=("Arial", 18))
label.pack(padx=20, pady=20)

def record_and_transcribe():
    button.config(state="disabled")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
        filename = tf.name
    messagebox.showinfo("Recording", "Recording will start in 3 seconds")
    duration = 120  # seconds
    sample_rate = 44100
    myrecording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    sf.write(filename, myrecording, sample_rate, format='wav')
    messagebox.showinfo("Recording", f"Recording saved to {filename}")
    model = whisper.load_model("large-v3")
    result = model.transcribe(filename)
    text = result["text"]
    pyperclip.copy(text)
    messagebox.showinfo("Transcription", f"Transcription: {text}\n\nCopied to clipboard")
    button.config(state="normal")

button = tk.Button(root, text="Record", font=("Arial", 14), command=record_and_transcribe)
button.pack(padx=20, pady=20)

stop_button = tk.Button(root, text="Stop recording", font=("Arial", 14)) # add the stop function
stop_button.pack(padx= 20, pady=20)

root.mainloop()