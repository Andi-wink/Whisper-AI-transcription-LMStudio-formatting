# Whisper AI Transcription with LMStudio Formatting

This project is a speech-to-text transcription tool that uses OpenAI's **Whisper Large v3 model** and a local AI server to generate and refine transcriptions. The tool is built in Python with a **Tkinter GUI** for recording and transcribing audio, designed specifically for email communication and professional use.

## Features

- **Audio Recording**: Record speech via GUI or hotkeys.
- **Whisper AI Transcription**: Converts speech to text using OpenAI's Whisper model.
- **Text Refinement**: Formats transcriptions for email-ready responses, including spell checks and content cleanup.
- **Clipboard Integration**: Automatically incorporates clipboard content for command-based modes.
- **Hotkey Support**: Easily start/stop recordings with global hotkeys.

## Hotkeys

- **Ctrl + Alt + A**: Record standard transcription.
- **Ctrl + Alt + Y**: Command-based transcription.

## Example Use Case

Easily record voice memos for emails, with refined and formatted transcriptions for professional communication in sales context:


**Transcription from Audio Recording**: Hey John, pleasure meeting you earlier. As we discussed, please find attached the presentations and the pricing. I'll get back in touch in two weeks time. Regards

**AI Refined text**:

Hi John,

Pleasure meeting you earlier. As we discussed, attached please find the presentation and pricing details. I look forward to being in touch again in two weeks.

Regards

## Requirements

- Python 3.9
- OpenAI's Whisper
- LMStudio






