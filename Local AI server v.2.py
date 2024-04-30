from openai import OpenAI
import pyperclip

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

def send_transcription(transcription, instruction_type):
    if instruction_type == "email":
        # Static variable to be added with every transcription
        additional_info = "give my message a spell check and format it as an email. Leave all of the words the same, unless there is a clear error."

        # Combine the transcription with the additional information
        full_transcription = transcription + "\n\n" + additional_info

        # Define the initial history with the system's role
        history = [
            {"role": "system",
             "content": "I will be sending you voice messages in either English or German that require conversion into text for emails in the language of the input message. It's essential to conduct a spell check to correct any typographical errors while preserving the exact phrasing of my messages, unless there are clear spelling mistakes. Please format these texts with appropriate line breaks to enhance readability for email communication. The responses should be crafted as if I, Andrew, am directly replying. Refrain from adding a subject line; I only need the refined, raw email text. Ensure that the wording remains unchanged to retain my original message's integrity, except in cases of evident typos."},
            {"role": "user",
             "content": full_transcription}  # Add the full transcription, including additional information
        ]
    elif instruction_type == "command":
        # Add your custom instructions here
        additional_info = "you are tasked with creating business emails written as Andrew based on the transcription given to you"
        full_transcription = transcription + "\n\n" + additional_info
        history = [
            {"role": "system",
             "content": ""},
            {"role": "user",
             "content": full_transcription}
        ]

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

    # Here, instead of appending to history and asking for new user input,
    # we return the AI's response. The loop is not needed anymore.
    print(f"AI Response: {ai_response}")

    pyperclip.copy(ai_response)
    return ai_response



# Example usage of the function:
transcription = "This is where your transcription text will go."
ai_response = send_transcription(transcription, "email")
print("\nAI Response:", ai_response)
