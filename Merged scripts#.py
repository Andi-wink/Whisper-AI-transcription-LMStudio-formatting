import os
import sys
import time
import json
import re
import fitz  # PyMuPDF
import logging
import ollama
import shutil

# ------------------------------------------------------------
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("script_debug.log"),
        logging.StreamHandler()
    ]
)

# ------------------------------------------------------------
# Check PyMuPDF version
version_info = fitz.version
if isinstance(version_info, str):
    version_str = version_info.strip()
elif isinstance(version_info, tuple):
    version_str = '.'.join(version_info).strip()
else:
    raise SystemExit("Cannot determine PyMuPDF version")

version_parts = version_str.split('.')
version_numbers = tuple(map(int, version_parts))

if version_numbers < (1, 19, 0):
    raise SystemExit("require PyMuPDF v1.19.0+")

# ------------------------------------------------------------
# Select PDF file (no PySimpleGUI). Use cmd arg or prompt user.
if len(sys.argv) == 2:
    fname = sys.argv[1]
else:
    fname = input("Enter the full path of the PDF file to process: ").strip()

if not fname or not os.path.isfile(fname):
    raise SystemExit("No valid file selected or file does not exist.")

base_filename = os.path.splitext(os.path.basename(fname))[0]
basedir = os.path.join(os.path.dirname(fname), base_filename + "_extracted")

if not os.path.exists(basedir):
    os.makedirs(basedir)

t0 = time.time()
doc = fitz.open(fname)
page_count = doc.page_count

# Extract pages, text, and images
print("Starting extraction from PDF...")
for pno in range(page_count):
    print(f"Processing page {pno + 1}/{page_count}...")
    page = doc.load_page(pno)

    # Create a directory for each page
    page_dir = os.path.join(basedir, f"page_{pno + 1}")
    if not os.path.exists(page_dir):
        os.makedirs(page_dir)

    # Save the entire page as an image
    pix = page.get_pixmap()
    page_image_file = os.path.join(page_dir, f"page_{pno + 1}.png")
    pix.save(page_image_file)

    # Extract text blocks from the page and save to a text file
    text_blocks = page.get_text("blocks")
    page_text = ''
    for block in text_blocks:
        block_text = block[4].strip()
        if block_text:
            page_text += block_text + '\n'

    if page_text:
        textfile = os.path.join(page_dir, f"page_{pno + 1}.txt")
        with open(textfile, "w", encoding="utf-8") as f:
            f.write(page_text)

    # Extract images from the page
    images = page.get_images(full=True)
    xreflist = []
    img_counter = 0

    for img in images:
        xref = img[0]
        if xref in xreflist:
            continue  # Skip if image xref is already processed

        img_counter += 1
        pix = fitz.Pixmap(doc, xref)
        if pix.n >= 5:  # CMYK: convert to RGB first
            pix = fitz.Pixmap(fitz.csRGB, pix)

        imgfile = os.path.join(page_dir, f"image_{img_counter}.png")
        pix.save(imgfile)
        xreflist.append(xref)

t1 = time.time()
print("Extraction completed")
print("Total time %g sec" % (t1 - t0))

# ------------------------------------------------------------
# AI Analysis Section
# ------------------------------------------------------------

def send_ai_request(chat_history, retries=3, delay=5):
    for attempt in range(1, retries + 1):
        try:
            response = ollama.chat(
                model='llama3.2-vision',
                messages=chat_history
            )
            return response
        except Exception as e:
            logging.error(f"Attempt {attempt}: AI interaction failed with error: {e}")
            if attempt < retries:
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error("All retry attempts failed.")
                return None

def analyze_full_page(file_path, directory):
    if not os.path.exists(file_path):
        logging.error(f"Selected image '{file_path}' does not exist.")
        return None, {}

    # Read the image file
    try:
        with open(file_path, 'rb') as img_file:
            image_data = img_file.read()
        logging.debug(f"Successfully read image '{file_path}'.")
    except Exception as e:
        logging.error(f"Failed to read image '{file_path}': {e}")
        return None, {}

    # Extract page number
    page_dir_name = os.path.basename(directory)
    try:
        if page_dir_name.startswith('page_'):
            page_number = int(page_dir_name.split('_')[1])
        else:
            logging.warning("Unable to determine page number. Defaulting to 1.")
            page_number = 1
    except ValueError:
        logging.warning("Invalid page number format. Defaulting to 1.")
        page_number = 1

    # Read associated text file
    text_file_path = os.path.join(directory, f"page_{page_number}.txt")
    if os.path.exists(text_file_path):
        try:
            with open(text_file_path, 'r', encoding='utf-8') as text_file:
                page_text = text_file.read()
            logging.debug(f"Page Text: {page_text[:100]}...")
        except Exception as e:
            logging.error(f"Failed to read text file '{text_file_path}': {e}")
            page_text = ''
    else:
        page_text = ''
        logging.warning(f"Text file '{text_file_path}' does not exist. Proceeding with empty text.")

    prompt = (
        f"You are analyzing an image on page {page_number} of a PDF work instruction document.\n"
        f"{page_text}\n\n"
        "Please perform the following tasks:\n\n"
        "1. Identify all images relevant to the tasks performed by the operator.\n\n"
        "2. For each identified image, provide:\n"
        "   - A label (`image_1`, `image_2`, etc.) based on their order.\n"
        "   - A title summarizing the main task or component in the image.\n"
        "   - A list of tasks associated with that image. These tasks may be related via context or proximity.\n"
        "   - A detailed description of the image itself, focusing solely on what can be directly observed (e.g., objects visible, colors, shapes, spatial arrangement). Do not reference or rely on any text from the document for this description.\n\n"
        "3. If no images are identified, return an empty `images` array.\n\n"
        "**Important Formatting Requirements:**\n\n"
        "- Your response must be a **valid JSON object**.\n"
        "- Do not include any text, explanations, reasoning, commentary, or text outside of the JSON object.\n"
        "- Do not use Markdown, bullet points, or any formatting outside the JSON structure.\n"
        "- Do not include any keys or fields not described.\n"
        "- Do not include any extra text after the closing brace of the JSON object.\n\n"
        "**Expected JSON Structure:**\n"
        "{\n"
        "  \"images\": [\n"
        "    {\n"
        "      \"label\": \"image_1\",\n"
        "      \"title\": \"Example Title\",\n"
        "      \"tasks\": [\n"
        "        \"Task 1\",\n"
        "        \"Task 2\"\n"
        "      ],\n"
        "      \"detailed_description\": \"A detailed step-by-step description focusing only on what is visually observable in the image.\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
    )

    chat_history = [{'role': 'user', 'content': prompt, 'images': [image_data]}]

    try:
        logging.info(f"Sending initial prompt to Ollama AI for '{os.path.basename(file_path)}'...")
        response = send_ai_request(chat_history)
        if response is None:
            logging.error("Failed to receive a response from AI after multiple attempts.")
            return chat_history, {}

        logging.debug(f"Raw AI Response: {response}")

        if isinstance(response, dict) and 'message' in response and 'content' in response['message']:
            response_text = response['message']['content']
        else:
            logging.warning("No 'message.content' field found in the AI response.")
            response_text = str(response)

        logging.info(f"AI Response for '{os.path.basename(file_path)}':\n{response_text}\n")
        logging.debug(f"Raw AI Response Text:\n{response_text}\n")

        # Attempt to extract JSON using a regex
        match = re.search(r'(\{(?:[^{}]|(?R))*\})', response_text, flags=re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            json_str = response_text.strip()

        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                images = data.get("images", [])
                return chat_history, {'images': images}
            else:
                logging.error("AI response JSON is not a dictionary.")
                logging.debug(f"AI Response JSON: {data}")
                return chat_history, {'images': []}
        except json.JSONDecodeError:
            logging.error("Failed to parse AI response as JSON.")
            logging.debug(f"Response Text: {response_text}")
            return chat_history, {'images': []}

    except Exception as e:
        logging.error(f"An error occurred during AI interaction: {e}")
        return None, {}

# Commented out image comparison / rename code as requested
# def check_and_rename_images(directory, data):
#     # No renaming logic as requested
#     pass

def main_analysis(root_dir):
    # Loop through each page directory
    page_dirs = [d for d in os.listdir(root_dir) if d.startswith('page_') and os.path.isdir(os.path.join(root_dir, d))]
    page_dirs.sort(key=lambda x: int(x.split('_')[1]))

    if not page_dirs:
        logging.error("No 'page_' directories found for analysis.")
        print("No 'page_' directories found for analysis.")
        return

    final_results = []

    for page_dir_name in page_dirs:
        directory = os.path.join(root_dir, page_dir_name)
        page_number = int(page_dir_name.split('_')[1])
        page_image_path = os.path.join(directory, f"page_{page_number}.png")

        if not os.path.exists(page_image_path):
            logging.warning(f"No page image found for {page_dir_name}. Skipping...")
            continue

        chat_history, data = analyze_full_page(page_image_path, directory)
        if chat_history is None:
            logging.error(f"Failed to analyze '{page_image_path}'. Skipping...")
            continue

        images_data = data.get('images', [])
        final_results.append((page_dir_name, images_data))

    # Print results in desired format
    for page_dir_name, images in final_results:
        print(f"\nPage: {page_dir_name}")
        print("**images**\n")
        if not images:
            print("No images identified.\n")
            continue
        for img in images:
            label = img.get('label', '')
            title = img.get('title', '')
            tasks = img.get('tasks', [])
            detailed_description = img.get('detailed_description', '')

            print(f"* **{label}**")
            print(f"\t+ title: {title}")
            if tasks:
                print("\t+ tasks:")
                for t in tasks:
                    print(f"\t   {t}")
            else:
                print("\t+ tasks: None")

            print(f"\t+ detailed description: {detailed_description}\n")

    print("Image analysis completed successfully.")

# After extraction is done, run the analysis on `basedir`.
main_analysis(basedir)
