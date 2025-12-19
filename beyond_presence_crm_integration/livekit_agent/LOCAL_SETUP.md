# Local Setup Guide

This guide explains how to run the entire LiveKit Agent and Web Interface locally on your machine.

## Prerequisites

1.  **Docker Desktop**: Required to run the local LiveKit Server. [Download here](https://www.docker.com/products/docker-desktop/).
2.  **Python 3.9+**: Required to run the agent.
3.  **OpenAI API Key**: Required for the agent's intelligence (STT/LLM/TTS).

## Step 1: Start Local LiveKit Server

The easiest way to run LiveKit locally is using Docker.

1.  Open your terminal/command prompt.
2.  Run the following command:

    ```bash
    docker run -p 7880:7880 -p 7881:7881 -p 7882:7882 livekit/livekit-server --dev --bind 0.0.0.0
    ```

    *   This starts a server at `ws://localhost:7880`.
    *   **Note**: The `--bind 0.0.0.0` flag is crucial for Docker to allow connections from your host machine.
    *   **Default API Key**: `devkey`
    *   **Default API Secret**: `secret`

## Step 2: Configure Environment

1.  Navigate to the `livekit_agent` directory.
2.  Copy `.env.example` to a new file named `.env`.
3.  Open `.env` and fill in your keys:

    ```properties
    # LiveKit Configuration (Already set for local)
    LIVEKIT_URL=ws://localhost:7880
    LIVEKIT_API_KEY=devkey
    LIVEKIT_API_SECRET=secret

    # OpenAI (Required)
    OPENAI_API_KEY=sk-...

    # Beyond Presence (Optional - for video avatar)
    # Leave empty for audio-only mode during local testing
    BEYOND_PRESENCE_API_KEY=...
    BEYOND_PRESENCE_AVATAR_ID=...
    ```

## Step 3: Run the Agent

1.  In a new terminal window (keep the Docker one running), navigate to `livekit_agent`.
2.  Install dependencies (if not already done):
    ```bash
    pip install -r requirements.txt
    ```
3.  Start the agent:
    ```bash
    python agent.py start
    ```
    *   You should see logs indicating it connected to `ws://localhost:7880`.

## Step 4: Use the Web Interface

1.  Open `index.html` in your browser (or use `python -m http.server`).
2.  Click the **Configuration (⚙️)** icon on the landing page.
3.  Enter the local details:
    *   **URL**: `ws://localhost:7880`
    *   **Token**: You need to generate a token.

### Generating a Token
Since we are running locally, we need to generate a token for the user to join.

1.  Create a file named `generate_token.py` (if it doesn't exist) with this content:
    ```python
    import os
    from livekit import api
    from dotenv import load_dotenv

    load_dotenv()

    # Local defaults if env vars missing
    URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
    API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
    API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")

    token = api.AccessToken(API_KEY, API_SECRET) \
        .with_identity("user-identity") \
        .with_name("Local User") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room="my-room",
        ))

    print(f"Token: {token.to_jwt()}")
    ```
2.  Run it: `python generate_token.py`
3.  Copy the printed token string.
4.  Paste it into the Web Interface **Token** field.
5.  Click **Save & Close**, then **Video Agent**.

You are now connected locally!
