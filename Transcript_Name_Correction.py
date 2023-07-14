import io
import itertools
import re
from difflib import SequenceMatcher
import streamlit as st
from streamlit.components.v1 import html
from docx import Document
from typing import List, Tuple

# Name Extractor for graduation ceremony in-person lists functions
def extract_middle_column_text(doc):
    middle_column_texts = []

    for table in doc.tables:
        for row in table.rows:
            cells = row.cells
            if len(cells) > 1:
                middle_cell = cells[len(cells) // 2]
                lines = middle_cell.text.split('\n')
                desired_text = ''
                inside_brackets = False  # Initialize bracket flag
                for line in lines:
                    line = line.strip()

                    # Update bracket flag
                    if line.startswith('('):
                        inside_brackets = True
                    if line.endswith(')'):
                        inside_brackets = False
                        continue

                    # Ignore lines inside brackets
                    if inside_brackets:
                        continue

                    # Ignore lines that contain full bracketed phrases
                    line = re.sub(r'\(.*?\)', '', line)
                    line = re.sub(r'\[.*?\]', '', line)

                    if line:
                        desired_text = line
                middle_column_texts.append(desired_text)

    return [decapitalize(text) for text in middle_column_texts if text != 'VACANT SEAT']

# Initialize names_list as an empty string
names_list = ''

# Use names_list as the default value for the names_list text_area
names_list = st.text_area("Enter names (separate names with commas):", ', '.join(names_list), key='names_list')

if names_list:  # Check if names_list is not empty
    names_list = names_list.split(',')
    names_list = [name.strip() for name in names_list]
    capitalized_names_list = [name.upper() for name in names_list]  # Create capitalized_names_list

#Correct all names in graduation transcript (find and replace) functions

def get_similar_names(text: str, name: str) -> List[str]:
    # Split the name into words
    name_words = name.split()

    # Create a regex pattern to match the name with optional whitespace between words
    pattern = r'\b' + r'\s*'.join(re.escape(word) for word in name_words) + r'\b'

    # Find all occurrences of the pattern in the text (case-insensitive)
    similar_names = re.findall(pattern, text, flags=re.IGNORECASE)

    # Remove duplicates and return the result
    return list(set(similar_names))

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def replace_similar_names(text: str, names_list: List[str]) -> Tuple[List[Tuple[str, str]], str]:
    replaced_names = []

    def replace_name(match):
        full_name = match.group(0)

        # Check if the name is already replaced
        for original, replaced in replaced_names:
            if full_name == replaced:
                return full_name

        max_similarity = 0
        most_similar_name = None
        for name in names_list:
            sim = similarity(full_name, name)
            if sim > max_similarity and len(full_name.split()) == len(name.split()): # Add condition here
                max_similarity = sim
                most_similar_name = name

        if max_similarity >= similarity_threshold:  # Use similarity_threshold here
            replaced_names.append((full_name, most_similar_name))
            return most_similar_name
        else:
            return full_name

    # Updated regex pattern
    pattern = r'\b([A-Z][a-z]+(?:(?: |-)[A-Z][a-z]+)*)\b'

    processed_lines = []
    lines = text.split('\n')
    for line in lines:
        # Skip timecode lines
        if re.match(r'\d\d:\d\d:\d\d\.\d\d\d\s*-->', line):
            processed_lines.append(line)
            processed_lines.append('')
            continue

        line = re.sub(pattern, replace_name, line)
        processed_lines.append(line)

    new_text = '\n'.join(processed_lines)

    if replaced_names:
        # Remove leading whitespaces from all lines as a final step
        new_text = '\n'.join(line.lstrip() for line in new_text.split('\n'))
        return replaced_names, new_text
    else:
        return [], ''

def decapitalize(text):
    roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI']
    words = text.split()
    for i, word in enumerate(words):
        if word not in roman_numerals:

            # Split hyphenated words and capitalize each part
            hyphen_parts = word.split('-')
            hyphen_parts = [part.lower().title() for part in hyphen_parts]
            word = '-'.join(hyphen_parts)

            # Split words with apostrophes and capitalize each part
            apostrophe_parts = word.split("'")
            apostrophe_parts = [part.lower().title() for part in apostrophe_parts]
            words[i] = "'".join(apostrophe_parts)

    return ' '.join(words)
        
#Name Corrector UI

st.header('Graduation Transcription Workflow Web Tool')

# Add a slider in the sidebar
similarity_threshold = st.sidebar.slider(
    'Set your similarity threshold. Lower values make name matching more lenient, higher values make it stricter. 0.65 or 0.7 recommended at first.',
    min_value=0.0,
    max_value=1.0,
    value=0.65,
    step=0.05,
)

# Add the banner image at the top of the app
st.image("banner.jpg")

st.title('Name Extractor for Graduation Ceremony In-Person Lists')

uploaded_file = st.file_uploader("Choose a Word document", type="docx")

if uploaded_file is not None:
    document = Document(io.BytesIO(uploaded_file.read()))
    names_list = extract_middle_column_text(document)  # Keep names_list as a list

st.title("Graduation Transcript Name Corrector")
# Initialize transcript_text as an empty string
transcript_text = ''

uploaded_transcript_file = st.file_uploader("Choose a VTT or text document for transcript", type=["vtt", "txt"])

if uploaded_transcript_file is not None:
    transcript_text = uploaded_transcript_file.read().decode()

# Use the transcript_text as the default value for the transcript text_area
text = st.text_area("Enter graduation transcript text:", transcript_text, key='transcript_text')

if st.button("Run"):  # Run button added
    if names_list and text:  # Check if both text boxes are populated
        replaced_names, new_text = replace_similar_names(text, names_list)

    if replaced_names and new_text:  # Check if replaced_names and new_text exist
        # Escape newline characters and single quotes in new_text
        escaped_new_text = new_text.replace('\n', '\\n').replace('\r', '\\r').replace("'", "\\'")

        # Button to copy the replaced text to the clipboard
        copy_button_html = f"""
        <button onclick="copyReplacedText()">Copy replaced text to clipboard</button>
        <script>
        function copyReplacedText() {{
            let text = '{escaped_new_text}';
            navigator.clipboard.writeText(text);
        }}
        </script>
        """
        html(copy_button_html, height=30)

    st.subheader("Names replaced:")
    for original, replaced in replaced_names:
        st.write(f"{original} -> {replaced}")

    st.text_area("Updated Transcript:", new_text, key='updated_transcript_text')
