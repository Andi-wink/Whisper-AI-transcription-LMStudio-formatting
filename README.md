# Whisper AI Transcription with LM Studio Integration

A modern, feature-rich voice transcription application that combines OpenAI's Whisper model with local AI processing through LM Studio/Ollama. Features a sleek, compact floating card interface with real-time voice activity detection and intelligent text processing.

![Whisper AI Transcription](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Whisper](https://img.shields.io/badge/Whisper-Large--v3-orange)

## ✨ Features

### 🎙️ Advanced Voice Recording
- **Real-time Voice Activity Detection** using WebRTC VAD
- **Variable-length recording** with automatic silence detection
- **GPU-accelerated transcription** with CUDA support
- **Multiple audio formats** support (WAV, MP3, MOV video files)
- **Hotkey support** for hands-free operation

### 🎨 Modern UI Design
- **Compact floating card interface** (400x500px)
- **Cherry Red theme** (#EF4444) with smooth hover effects
- **Live waveform visualization** with 12 animated bars
- **Real-time recording status** and timer display
- **Glassmorphic design** with gradient backgrounds

### 🤖 AI Integration
- **Local AI processing** via Ollama/LM Studio
- **Intelligent text formatting** for emails and notes
- **Multi-language support** (English/German)
- **Clipboard integration** with previous content preservation
- **Automatic spell-check** and phrase refinement

### ⚡ Smart Features
- **Hotkey combinations** for different transcription modes
- **Email formatting** mode for professional communication
- **Notes generation** with bullet-point formatting
- **File transcription** support for audio/video files
- **Memory-efficient processing** with automatic cleanup

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- NVIDIA GPU (recommended) with CUDA support
- Ollama or LM Studio running locally
- Windows OS (for clipboard functionality)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Andi-wink/Whisper-AI-transcription-LMStudio-formatting.git
cd Whisper-AI-transcription-LMStudio-formatting
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up Ollama/LM Studio:**
   - Install [Ollama](https://ollama.ai/) or [LM Studio](https://lmstudio.ai/)
   - Download a compatible model (e.g., `gemma3:4b`)
   - Ensure the service is running on `localhost:11434` (Ollama) or configure accordingly

4. **Run the application:**
```bash
python Whisper_AI_transcription.py
```

## 🎯 Usage

### Hotkey Controls
- **Ctrl+Alt+A**: Quick transcription and paste
- **Ctrl+Alt+X**: Generate formatted notes
- **Ctrl+Alt+Y**: Email formatting mode
- **Ctrl+Alt+F**: Paste with previous clipboard content

### Recording Modes
1. **Voice Recording**: Click the microphone button or use hotkeys
2. **File Transcription**: Use the file selector button for audio/video files
3. **Variable Length**: Automatic recording with silence detection

### AI Processing
The application sends transcriptions to your local AI model with intelligent prompts for:
- Email formatting and spell-checking
- Note generation with bullet points
- Multi-language text refinement
- Professional communication enhancement

## 📁 Project Structure

```
├── Whisper_AI_transcription.py    # Main application
├── Local_AI_server.py             # AI integration module
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── .gitignore                     # Git ignore rules
```

## ⚙️ Configuration

### AI Model Settings
Edit `Local_AI_server.py` to configure:
- **API Endpoint**: Default `http://localhost:11434/api/chat`
- **Model Name**: Default `gemma3:4b`
- **Temperature**: Default `0.7`

### Audio Settings
Modify in `Whisper_AI_transcription.py`:
- **Sample Rate**: Default `16000 Hz`
- **Recording Duration**: Default `30 seconds max`
- **Silence Detection**: Default `3 seconds`
- **VAD Aggressiveness**: Default level `3`

## 🔧 Technical Details

### Dependencies
- **transformers**: Hugging Face transformers for Whisper
- **torch**: PyTorch for GPU acceleration
- **sounddevice**: Real-time audio recording
- **webrtcvad**: Voice activity detection
- **moviepy**: Video file processing
- **tkinter**: GUI framework
- **pyperclip**: Clipboard operations

### GPU Acceleration
The application automatically detects and uses CUDA-enabled GPUs for:
- Faster Whisper model inference
- Reduced transcription latency
- Memory-efficient processing

### Voice Activity Detection
Uses WebRTC VAD for intelligent recording:
- Automatic start/stop based on voice presence
- Configurable sensitivity levels
- Fallback to amplitude-based detection

## 🐛 Troubleshooting

### Common Issues

**CUDA Not Available:**
- Ensure NVIDIA drivers are installed
- Verify PyTorch CUDA installation: `torch.cuda.is_available()`
- Check GPU compatibility with CUDA

**Audio Recording Issues:**
- Verify microphone permissions
- Check default audio device settings
- Install `webrtcvad`: `pip install webrtcvad`

**AI Connection Problems:**
- Ensure Ollama/LM Studio is running
- Verify API endpoint in `Local_AI_server.py`
- Check model availability: `ollama list`

**Hotkeys Not Working:**
- Run as administrator (Windows)
- Check for conflicting hotkey assignments
- Verify `keyboard` module installation

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the Whisper speech recognition model
- Hugging Face for the transformers library
- The Ollama team for local AI inference
- WebRTC project for voice activity detection

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/Andi-wink/Whisper-AI-transcription-LMStudio-formatting/issues) page
2. Create a new issue with detailed information
3. Include system specifications and error logs

---

**Made with ❤️ for seamless voice-to-text transcription**
