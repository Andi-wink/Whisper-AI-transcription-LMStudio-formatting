import requests
import json
import pyperclip

# Ollama API endpoint (default is localhost:11434)
OLLAMA_API_URL = "http://localhost:11434/api/chat"
# Model name to use (Gemma3n as requested)
MODEL_NAME = "gemma3:4b"


def send_transcription(transcription, content, additional_content=None):
    # Define the initial history with the system's role
    messages = [
        {"role": "system", "content": content},
        {"role": "user", "content": transcription}
    ]

    if additional_content:
        messages.append({"role": "user", "content": additional_content})

    # Prepare the request payload
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.7
        }
    }

    print(f"Sending request to Ollama ({MODEL_NAME})...")
    
    # Make streaming request to Ollama API
    response = requests.post(
        OLLAMA_API_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    # Initialize a variable to hold the AI's response
    ai_response = ""
    
    # Process the streaming response
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    if "message" in json_response and "content" in json_response["message"]:
                        chunk = json_response["message"]["content"]
                        print(chunk, end="", flush=True)
                        ai_response += chunk
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
    else:
        print(f"Error: Received status code {response.status_code} from Ollama API")
        print(response.text)
        return f"Error: Failed to get response from Ollama (status code: {response.status_code})"

    # Define unwanted starting phrases
    unwanted_starts = [
        "Here is the converted text:",
        "Here's the refined text:",
        "Here is the refined text",
        "Here is the refined email text:"
    ]

    # Check and remove any unwanted starting phrase
    for phrase in unwanted_starts:
        if ai_response.startswith(phrase):
            ai_response = ai_response[len(phrase):].strip()

    # Return the AI's response
    print(f"AI Response: {ai_response}")
    pyperclip.copy(ai_response)
    return ai_response


# Example usage of the function:
if __name__ == "__main__":
    transcription = "This is where your transcription text will go."
    content = "I will be sending you voice messages in either English or German that require conversion into text for emails in the language of the input message. It's essential if the input is English it remains English. The same applies if the input is German, keep it German. Conduct a spell check to correct any typographical errors while preserving the exact phrasing of my messages, unless there are clear spelling mistakes. Please format these texts with appropriate line breaks to enhance readability for email communication. The responses should be crafted as if I, Andrew, am directly replying. Refrain from adding a subject line; I only need the refined, raw email text. Ensure that the wording remains mostly unchanged to retain my original message's integrity, but improve certain phrases and ammend evident typos. Don't not add: Here is the converted text: at the beginning of your reply. If there is you you or you at the the end of the transcription remove it"
    additional_content = "This is the additional content from the clipboard."
    ai_response = send_transcription(transcription, content, additional_content)
    print("\nAI Response:", ai_response)
