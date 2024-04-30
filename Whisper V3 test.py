import torch
import time
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

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
    chunk_length_s=9,
    batch_size=32,
    return_timestamps=True,
    torch_dtype=torch_dtype,
    device=device,
)

# Define the path to the local MP3 file
file_path = r"C:\Users\andre\Documents\VKS\Audio test\tmptuu2ambq.wav"


# Start the timer
start_time = time.time()

# Transcribe the audio file
result = pipe(file_path)

# End the timer
end_time = time.time()

# Calculate the elapsed time
elapsed_time = end_time - start_time

# Print the transcription result
print(result["text"])

# Print the total execution time
print(f"Total execution time: {elapsed_time:.2f} seconds")



