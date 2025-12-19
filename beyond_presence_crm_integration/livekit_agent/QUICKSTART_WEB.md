# Quickstart: Insurance Support Agent Web Interface

This guide explains how to view and use the new Insurance Support Agent web interface.

## 1. Viewing the Webpage

The web interface is a single self-contained HTML file. You do not need a complex build server to view it.

### Option A: Direct Open (Simplest)
1.  Navigate to the `livekit_agent` folder in your file explorer.
2.  Double-click `index.html`.
3.  It will open in your default web browser.

### Option B: Live Server (Recommended for Development)
If you have a VS Code extension like "Live Server" or Python installed:
1.  Open a terminal in the `livekit_agent` directory.
2.  Run: `python -m http.server 8000`
3.  Open your browser to `http://localhost:8000`

## 2. Using the Interface

### Landing Page
-   **Voice Agent**: Select this for an audio-only experience. The interface will show a pulsing visualizer.
-   **Video Agent**: Select this for the full Beyond Presence avatar experience.
-   **Configuration (⚙️)**: Click the small gear icon to enter your LiveKit Server URL and Token.

### Agent Interface
-   **Video Area**: Shows the avatar (in Video mode) or visualizer (in Voice mode).
-   **Chat**: Type messages in the floating chat box to interact via text.
-   **Controls**:
    -   🎤 **Mute**: Toggle your microphone.
    -   📞 **End Call**: Disconnect and return to the landing page.

## 3. Connecting to a Real Agent
To make the agent actually work, you need to run the backend agent and generate a token.

1.  **Start your LiveKit Server** (locally or cloud).
2.  **Run the Agent**:
    ```bash
    python agent.py start
    ```
3.  **Generate a Token**:
    Use the `generate_token.py` script (if available) or LiveKit CLI to generate a token for the room.
4.  **Enter Token**: Paste this token into the Configuration menu on the webpage.
