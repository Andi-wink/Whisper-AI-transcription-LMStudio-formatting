from openai import OpenAI
import pyperclip

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")


def send_transcription(transcription, content, additional_content=None):
    # Define the initial history with the system's role
    history = [
        {"role": "system", "content": content},
        {"role": "user", "content": transcription},  # Add the transcription directly as the user's content
    ]

    if additional_content:
        history.append({"role": "user",
                        "content": additional_content})  # Add the additional content from the clipboard only if present

    # Request a completion from the local AI model
    completion = client.chat.completions.create(
        model="local-model",  # This field is currently unused but set for potential future use
        messages=history,
        temperature=0.7,
        stream=True,
    )

    # Initialize a variable to hold the AI's response
    ai_response = ""

    # Iterate through the completion to get the AI's response
    for chunk in completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
            ai_response += chunk.choices[0].delta.content

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
