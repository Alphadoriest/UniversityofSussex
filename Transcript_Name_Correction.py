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
from streamlit import components

# Name Extractor for graduation ceremony in-person lists functions
def extract_middle_column_text(doc):
    middle_column_texts = []

    for table in doc.tables:
        for row in table.rows:
            cells = row.cells
            if len(cells) > 1:
                middle_cell = cells[len(cells) // 2]
                paragraphs = middle_cell.paragraphs
                desired_text = ''
                inside_brackets = False  # Initialize bracket flag
                for paragraph in paragraphs:
                    clean_paragraph_text = ''
                    for run in paragraph.runs:
                        if not run.font.strike:  # If the text is not strikethrough
                            clean_paragraph_text += run.text  # append the text of run to the clean_paragraph_text
                    lines = clean_paragraph_text.split('\n')
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

    # Join the text with ', ', then replace ', ,' with ', ', and finally split again by ', '
    cleaned_text = re.sub(r'(,\s*)+', ', ', ', '.join(middle_column_texts))  # Replace multiple commas with a single comma
    return [decapitalize(text) for text in cleaned_text.split(', ') if text not in ["VACANT SEAT", "Vacant Seat", "Carer's seat", "CARER'S SEAT", "Child", "CHILD"]]

def format_names(names_list):
    colors = ['red', 'green', 'blue', 'yellow']  # Add more colors if needed
    formatted_names = []
    for i, name in enumerate(names_list):
        color = colors[i % len(colors)]
        formatted_name = (name, color)
        formatted_names.append(formatted_name)
    return formatted_names

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

    # Calculate overall similarity
    overall_similarity = sequence_weight * sequence_similarity + fuzz_weight * fuzz_similarity + metaphone_weight * metaphone_similarity

    # Apply penalty if one name is a single word and the other is multi-word
    if (len(a.split()) == 1 and len(b.split()) > 1) or (len(a.split()) > 1 and len(b.split()) == 1):
        penalty_factor = 0.75  # Adjust this value to increase or decrease the penalty
        overall_similarity *= penalty_factor

    return overall_similarity

def replace_similar_names(text: str, names_list: List[str]) -> Tuple[List[Tuple[str, str]], str]:
    replaced_names = []
    unmatched_names = names_list[:]  # Make a copy of names_list

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
            if sim > max_similarity and (not match_word_count or len(full_name.split()) == len(name.split())):
                max_similarity = sim
                most_similar_name = name
    
        if max_similarity >= similarity_threshold:
            replaced_names.append((full_name, most_similar_name))
            # Remove the name from unmatched_names if it was matched
            if most_similar_name in unmatched_names:
                unmatched_names.remove(most_similar_name)
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
            continue

        line = re.sub(pattern, replace_name, line)
        processed_lines.append(line)

    new_text = '\n'.join(processed_lines)

    if replaced_names:
        # Remove leading whitespaces from all lines as a final step
        new_text = '\n'.join(line.lstrip() for line in new_text.split('\n'))
        return replaced_names, new_text, unmatched_names  # Return unmatched_names as well
    else:
        return [], '', unmatched_names  # Return unmatched_names as well

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

def reformat_transcript(text: str, replaced_names: List[Tuple[str, str]]) -> str:
    replaced_names_dict = {replaced: original for original, replaced in replaced_names}  # reversed mapping

    if text.startswith('WEBVTT'):
        text = text.replace('WEBVTT', 'WEBVTT\n', 1)

    blocks = re.split(r'(\d\d:\d\d:\d\d\.\d\d\d --> \d\d:\d\d:\d\d\.\d\d\d)', text)
    formatted_blocks = []

    for block in blocks:
        if re.match(r'\d\d:\d\d:\d\d\.\d\d\d --> \d\d:\d\d:\d\d\.\d\d\d', block):
            formatted_blocks.append(block.strip() + '\n')
            continue

        lines = block.split('\n')
        lines = [line for line in lines if line.strip()]

        formatted_lines = []
        for line in lines:
            words = line.split()
            if words:
                for replaced in replaced_names_dict.keys():
                    replaced_words = replaced.split()
                    if len(words) >= len(replaced_words):
                        last_words = words[-len(replaced_words):]
                        if ' '.join(last_words) == replaced and not last_words[-1].endswith('.'):
                            words[-1] = words[-1] + '.'

                formatted_line = ' '.join(words)
                formatted_line = re.sub(r'\[no audio\]', '', formatted_line, flags=re.IGNORECASE)
                formatted_line = re.sub(r'\[applause\]', '[Applause]', formatted_line, flags=re.IGNORECASE)
                formatted_line = re.sub(r'\((applause)\)', '[Applause]', formatted_line, flags=re.IGNORECASE)
                formatted_line = re.sub(r'\((Music|MUSIC|MUSIC PLAYING)\)|\[(Music|MUSIC|MUSIC PLAYING)\]', '[Music Playing]', formatted_line, flags=re.IGNORECASE)
                formatted_line = re.sub(r'\((laughter)\)|\[laughter\]', '[Audience Laughing]', formatted_line, flags=re.IGNORECASE)
                formatted_line = re.sub(r'\((cheering|audience cheering)\)|\[(cheering|audience cheering)\]', '[Audience Cheers]', formatted_line, flags=re.IGNORECASE)
                formatted_line = re.sub(r'\((shouting|audience shouting)\)|\[(shouting|audience shouting)\]', '[Audience Shouts]', formatted_line, flags=re.IGNORECASE)
                formatted_lines.append(formatted_line)

        formatted_block = '\n'.join(formatted_lines)
        formatted_block += '\n\n' if formatted_block and block != blocks[-1] else '\n'
        formatted_blocks.append(formatted_block)

    return ''.join(formatted_blocks)

def find_best_match(transcript, preceding, succeeding):
    # Get the positions of preceding and succeeding names
    preceding_position = transcript.find(preceding)
    succeeding_position = transcript.find(succeeding)

    if preceding_position != -1 and succeeding_position != -1:
        # Extract the text between the two positions
        between_text = transcript[preceding_position + len(preceding):succeeding_position]

        # Split the text into words
        words = between_text.split()

        # Find the word with the maximum similarity to the unmatched name
        best_match = max(words, key=lambda word: similarity(word, unmatched))

        return best_match
    else:
        return None
        
#Name Corrector UI

st.title('Graduation Transcription Workflow Web Tool')

# Add a slider in the sidebar
st.sidebar.header('Set Overall Similarity Threshold for Combined Methods')
similarity_threshold = st.sidebar.slider(
    'Set your similarity threshold. Lower values make name matching more lenient, higher values make it stricter. When equally weighted, 0.45-0.6 gives acceptable output.',
    min_value=0.0,
    max_value=1.0,
    value=0.45,
    step=0.01,
)

# Slider weights
st.sidebar.header('Adjust Weights for Comparison Methods')
st.sidebar.text('Set the relative weights of each method towards the name similarity matching - experimental.')
sequence_weight = st.sidebar.slider ('SequenceMatcher Weight', 0.0, 1.0, 0.33, 0.01)
fuzz_weight = st.sidebar.slider ('Fuzz Ratio Weight', 0.0, 1.0, 0.33, 0.01)
metaphone_weight = st.sidebar.slider ('Double Metaphone Weight', 0.0, 1.0, 0.34, 0.01)

# Ensure the sum of weights equal to 1
if sequence_weight + fuzz_weight + metaphone_weight != 1.0:
    st.sidebar.error('Please adjust the weights so their sum equals to 1.0')

# Match Word Count UI
st.sidebar.header('Match Word Count')
st.sidebar.text('Turning on ensures less mismatching, but more necessary if only relying on SequenceMatcher.')
match_word_count = st.sidebar.checkbox('Should the number of words match?', value=False)

# Add the banner image at the top of the app
st.image("banner.jpg")

st.header('Name Extractor for Graduation Ceremony In-Person Lists')

uploaded_file = st.file_uploader("Choose a Ceremony In-Person List Word document", type="docx")

# Initialize names_list as an empty string
names_list = ''

if uploaded_file is not None:
    document = Document(io.BytesIO(uploaded_file.read()))
    names_list = extract_middle_column_text(document)  # Keep names_list as a list

# Use names_list as the default value for the names_list text_area
names_list = st.text_area("Alternatively, enter names, separated by commas:", ', '.join(names_list), key='names_list')

if names_list:  # Check if names_list is not empty
    names_list = names_list.split(',')
    names_list = [name.strip() for name in names_list]
    # Check if names_list contains meaningful entries
    if any(name for name in names_list):

# Assuming format_names now returns a list of tuples like [(name, color), ...]
        formatted_names = format_names(names_list)
    
# Convert the list of tuples to a single string with HTML tags 
# Create the HTML div and set its height
        html_names = '<div style="height: 600px; overflow-y: auto;">' + ''.join([f'<span style="color:{color}; margin-right: 10px;"><strong><u>{name}</u></strong></span>' if len(name.split()) > 4 or len(name.split()) < 2 else f'<span style="color:{color}; margin-right: 10px;">{name}</span>' for name, color in formatted_names]) + '</div>'
            
# Display the HTML
        components.v1.html(html_names, height=600)
        st.text("Visualise potential errors. Number of names <2 or >4 = bold and underlined.")

st.header("Graduation Transcript Name Corrector")
# Initialize transcript_text as an empty string
transcript_text = ''

uploaded_transcript_file = st.file_uploader("Choose a VTT or TXT Transcript File ", type=["vtt", "txt"])
if uploaded_transcript_file is not None:
    transcript_text = uploaded_transcript_file.read().decode()

# Use the transcript_text as the default value for the transcript text_area
text = st.text_area("Alternatively, Enter Text From a Transcript:", transcript_text, key='transcript_text')

# Initialize preceding_names and succeeding_names as empty lists
preceding_names = []
succeeding_names = []

# Add a separate button for the name replacement process
if st.button("Press to Replace Names"):  
    if names_list and text:  # Check if both text boxes are populated
        replaced_names, new_text, unmatched_names = replace_similar_names(text, names_list)  # Unpack unmatched_names
        
        # Store the resultant text and replaced_names and unmatched_names in session state
        st.session_state.new_text = new_text  
        st.session_state.replaced_names = replaced_names
        st.session_state.unmatched_names = unmatched_names

# Display replaced and unmatched names from session state
if 'replaced_names' in st.session_state and st.session_state.replaced_names:
    st.subheader("Names replaced:")
    for original, replaced in st.session_state.replaced_names:
        original_words = original.split()
        replaced_words = replaced.split()

        # Check if the original and replaced names have a different number of words
        if len(original_words) != len(replaced_words):
            # If they do, make the text bold
            st.markdown(f"**{original} -> {replaced}**")
        else:
            st.write(f"{original} -> {replaced}")

if 'unmatched_names' in st.session_state:
    for preceding, succeeding, unmatched in zip(preceding_names, succeeding_names, st.session_state.unmatched_names):
        best_match = find_best_match(st.session_state.new_text, preceding, succeeding)
        if best_match is not None:
            st.write(f"Best match for {unmatched} is {best_match}")
        else:
            st.write(f"No match found for {unmatched}")

st.subheader("Names not matched:")
st.text("These can be addressed in one of two ways. Either copy the comma separated list and run just those names in another instance of the app at a lower threshold or browser search for the names surrounding the unmatched name and paste in the correct name in the updated transcript text box. The app will reset after each addition, but all progress is saved.")
if 'unmatched_names' in st.session_state:
    unmatched_names_str = ', '.join(st.session_state.unmatched_names)
    st.write(unmatched_names_str)

# Button to copy unmatched names to clipboard
if 'unmatched_names' in st.session_state:
    unmatched_names_str = ', '.join(st.session_state.unmatched_names)
    copy_unmatched_names_button_html = f"""
        <button onclick="copyUnmatchedNames()">Copy unmatched names to clipboard</button>
        <script>
        function copyUnmatchedNames() {{
            navigator.clipboard.writeText("{unmatched_names_str}");
        }}
        </script>
        """
    components.v1.html(copy_unmatched_names_button_html, height=30)

# Get the indices of unmatched names in names_list
if 'unmatched_names' in st.session_state:
    unmatched_indices = [names_list.index(name) for name in st.session_state.unmatched_names if name in names_list]

# Get the names that precede the unmatched names
# Get the names that succeed the unmatched names
if 'unmatched_names' in st.session_state:
    preceding_names = [names_list[i-1] if i > 0 else None for i in unmatched_indices]
    succeeding_names = [names_list[i+1] if i < len(names_list) - 1 else None for i in unmatched_indices]

if 'unmatched_names' in st.session_state:
        st.subheader("Preceding and Succeeding Names for Easy Look Up of Unmatched Name for Addition to Updated Transcript Box:")
        for preceding, succeeding, unmatched in zip(preceding_names, succeeding_names, st.session_state.unmatched_names):
            st.write(f"{preceding or 'N/A'}, {succeeding or 'N/A'} -> {unmatched}")

# Display the text area for the transcript
new_text = st.text_area("Updated Transcript Text to Copy Into VTT/TXT File:", st.session_state.new_text, key='updated_transcript_text')

# Update session state with any changes made in the text area
st.session_state.new_text = new_text

# Button to copy the replaced text to the clipboard
copy_button_html = f"""
    <button onclick="copyReplacedText()">Copy replaced text to clipboard</button>
    <script>
    function copyReplacedText() {{
        let text = document.getElementById('updated_transcript_text').value;
        navigator.clipboard.writeText(text);
    }}
    </script>
    """
components.v1.html(copy_button_html, height=30)
