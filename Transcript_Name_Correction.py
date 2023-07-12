import io
import itertools
import re
from difflib import SequenceMatcher
import streamlit as st
from streamlit.components.v1 import html
from docx import Document

#Name Extractor from graduation ceremony in-person lists
def extract_middle_column_text(doc):
    middle_column_texts = []

    for table in doc.tables:
        for row in table.rows:
            cells = row.cells
            if len(cells) > 1:
                middle_cell = cells[len(cells) // 2]
                # Split the text into lines
                lines = middle_cell.text.split('\n')
                # Initialize desired text as empty string
                desired_text = ''
                for line in lines:
                    line = line.strip()
                    # If line contains bracketed text or starts with a bracket, break the loop
                    if line.startswith('(') or re.search(r'\[.*\]', line):
                        break
                    # If line is non-empty, update the desired text
                    if line:
                        desired_text = line
                middle_column_texts.append(desired_text)

    # Remove 'VACANT SEAT' instances
    middle_column_texts = [text for text in middle_column_texts if text != 'VACANT SEAT']

    # Decapitalize text with exceptions
    def decapitalize(text):
        words = text.split()
        for i, word in enumerate(words):
            if word != 'I' and not (word.endswith(',') and word[:-1].isupper()):
                words[i] = word[0].upper() + word[1:].lower()
        return ' '.join(words)

    middle_column_texts = [decapitalize(text) for text in middle_column_texts]

    return ', '.join(middle_column_texts)

st.title('Name Extractor from graduation ceremony in-person lists')

uploaded_file = st.file_uploader("Choose a Word document", type="docx")

# Initialize extracted_text as an empty string
extracted_text = ''

if uploaded_file is not None:
    if st.button("Extract Names"):
        document = Document(io.BytesIO(uploaded_file.read()))
        extracted_text = extract_middle_column_text(document)
        names_list = st.text_area("Enter names (separate names with commas):", extracted_text).split(',')

# Use the extracted_text as the default value for the names_list text_area
names_list = st.text_area("Enter names (separate names with commas):", extracted_text).split(',')
names_list = [name.strip() for name in names_list]

#Correct all names in graduation transcript

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def replace_similar_names(text, names_list):
    full_name_pattern = re.compile(r'(?<!:)(?:\b\w+(?:\s+\w+){1,4}\b)(?!\d)')
    replaced_names = []

    lines = text.split('\n')
    processed_lines = []

    def replace_name(match):
        full_name = match.group(0)
        max_similarity = 0
        most_similar_name = None
        for name in names_list:
            sim = similarity(full_name, name)
            if sim > max_similarity:
                max_similarity = sim
                most_similar_name = name

        if max_similarity >= 0.8:  # Adjust the similarity threshold as needed
            replaced_names.append((full_name, most_similar_name))
            most_similar_name = most_similar_name.replace('"', '').replace(',', '')
            return most_similar_name
        else:
            return full_name

    for line in lines:
        # Skip timecode lines
        if re.match(r'\d\d:\d\d:\d\d\.\d\d\d\s*-->', line):
            processed_lines.append(line)
            processed_lines.append('')
            continue

        line = full_name_pattern.sub(replace_name, line)
        processed_lines.append(line)

    return replaced_names, '\n'.join(processed_lines)

st.title("Graduation Transcript Name Corrector")
# Initialize transcript_text as an empty string
transcript_text = ''

uploaded_transcript_file = st.file_uploader("Choose a VTT or text document for transcript", type=["vtt", "txt"])

# Initialize transcript_text as an empty string
transcript_text = ''

if uploaded_transcript_file is not None:
    if st.button("Load Transcript"):
        transcript_text = uploaded_transcript_file.read().decode()

# Use the transcript_text as the default value for the transcript text_area
text = st.text_area("Enter graduation transcript text:", transcript_text)

replaced_names, new_text = replace_similar_names(text, names_list)

st.subheader("Names replaced:")
for original, replaced in replaced_names:
    st.write(f"{original} -> {replaced}")

# Escape newline characters and single quotes in new_text
escaped_new_text = new_text.replace('\n', '\\n').replace('\r', '\\r').replace("'", "\\'")

# Add a button to copy the replaced text to the clipboard
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
