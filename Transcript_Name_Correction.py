import io
import itertools
import re
from difflib import SequenceMatcher
import streamlit as st
from streamlit.components.v1 import html
from docx import Document
from typing import List, Tuple
from fuzzywuzzy import fuzz
from metaphone import doublemetaphone

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
    sequence_similarity = SequenceMatcher(None, a, b).ratio()
    fuzz_similarity = fuzz.ratio(a, b) / 100.0
    metaphone_similarity = doublemetaphone(a) == doublemetaphone(b)

    # Adjust the weights here depending on the slider values
    return sequence_weight * sequence_similarity + fuzz_weight * fuzz_similarity + metaphone_weight * metaphone_similarity

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
            if sim > max_similarity and len(full_name.split()) == len(name.split()):
                max_similarity = sim
                most_similar_name = name
    
        if max_similarity >= similarity_threshold_slider.value:
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

st.title('Graduation Transcription Workflow Web Tool')

# Add a slider in the sidebar
# Default slider values
DEFAULT_THRESHOLD = 0.65
DEFAULT_SEQUENCE = 0.33
DEFAULT_FUZZ = 0.33  
DEFAULT_METAPHONE = 0.34

st.sidebar.title('Set Overall Similarity Threshold for Combined Methods')
similarity_threshold_slider = st.sidebar.slider(
  "Set your similarity threshold. Lower values make name matching more lenient, higher values make it stricter. 0.65 or 0.7 recommended at first.",
  min_value=0.0,
  max_value=1.0,
  value=DEFAULT_THRESHOLD,
  step=0.01
)

# Slider weights
st.sidebar.title('Adjust Weights for Comparison Methods')
st.sidebar.text('Set the relative weights of each method towards the name similarity matching - experimental.')
sequence_weight_slider = st.sidebar.slider('SequenceMatcher Weight', 0.0, 1.0, DEFAULT_SEQUENCE, 0.01)
fuzz_weight_slider = st.sidebar.slider('Fuzz Ratio Weight', 0.0, 1.0, DEFAULT_FUZZ, 0.01)
metaphone_weight_slider = st.sidebar.slider('Double Metaphone Weight', 0.0, 1.0, DEFAULT_METAPHONE, 0.01)

# Ensure the sum of weights equal to 1
# Use slider object values 
if sequence_weight_slider.value + fuzz_weight_slider.value + metaphone_weight_slider.value != 1.0:
  st.error("Weights must sum to 1.0")

# Reset button
if st.sidebar.button("Reset Weights"):
    similarity_threshold_slider.value = 0.65
    sequence_weight_slider.value = 0.33
    fuzz_weight_slider.value = 0.33
    metaphone_weight_slider.value = 0.34

# Add the banner image at the top of the app
st.image("banner.jpg")

st.header('Name Extractor for Graduation Ceremony In-Person Lists')

uploaded_file = st.file_uploader("Choose a Word document", type="docx")

# Initialize names_list as an empty string
names_list = ''

if uploaded_file is not None:
    document = Document(io.BytesIO(uploaded_file.read()))
    names_list = extract_middle_column_text(document)  # Keep names_list as a list

# Use names_list as the default value for the names_list text_area
names_list = st.text_area("Enter names (separate names with commas):", ', '.join(names_list), key='names_list')

if names_list:  # Check if names_list is not empty
    names_list = names_list.split(',')
    names_list = [name.strip() for name in names_list]
    capitalized_names_list = [name.upper() for name in names_list]  # Create capitalized_names_list

st.header("Graduation Transcript Name Corrector")
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
