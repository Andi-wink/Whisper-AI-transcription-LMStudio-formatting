def format_as_email(text):
    # Split the text into lines
    lines = text.split('\n')

    # Initialize variables
    formatted_lines = []
    in_body = False

    # Iterate through each line
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Check for email header fields
        if line.startswith(('From:', 'To:', 'Subject:', 'Date:')):
            formatted_lines.append(line.strip())
        else:
            # If the line doesn't start with a header field, it's part of the email body
            if not in_body:
                # Add a blank line before the email body
                formatted_lines.append('')
                in_body = True

            # Remove "you" or "you you" from the end of the line
            line = line.strip()
            if line.endswith('you you'):
                line = line[:-7].strip()
            elif line.endswith('you'):
                line = line[:-3].strip()

            # Add the line to the email body
            formatted_lines.append(line)

    # Join the formatted lines with line breaks
    formatted_email = '\n'.join(formatted_lines)

    return formatted_email

# Example usage
unformatted_text_1 = '''
Hallo Herr Hilgers, ich habe Sie leider diese Woche nicht erreicht. Wollen Sie eine Zeit festlegen für nächste Woche mal oder einen 15 Minuten Termin planen und das Gespräch online führen. Freundliche Grüße. you
'''

unformatted_text_2 = '''
Hi Paul, I've got a training planned in with you right now for VKS. Will you be joining me or does another time suit you better? Kind regards, Andrew. you you
'''

unformatted_text_3 = '''
Hi Diego, since I haven't heard back from you, I just wanted to suggest two more options we could try. you you
'''

unformatted_text_4 = '''
Hi Kevin, sounds good to me. I just sent the questions across already because if it's more complex IT stuff I might not know the answer in the meeting. Which is fine for me. But if you prefer to flesh it out a bit before, I can already bring some more answers when we speak. Kind regards, Andrew. you
'''

formatted_email_1 = format_as_email(unformatted_text_1)
formatted_email_2 = format_as_email(unformatted_text_2)
formatted_email_3 = format_as_email(unformatted_text_3)
formatted_email_4 = format_as_email(unformatted_text_4)

print("Formatted Email 1:")
print(formatted_email_1)
print("\nFormatted Email 2:")
print(formatted_email_2)
print("\nFormatted Email 3:")
print(formatted_email_3)
print("\nFormatted Email 4:")
print(formatted_email_4)