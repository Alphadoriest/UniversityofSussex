import re
from difflib import SequenceMatcher
import streamlit as st
from streamlit.components.v1 import html

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

st.title("Name Replacer")

names_list = st.text_area("Enter names (one per line):", "").split('\n')
text = st.text_area("Enter text:", "")

replaced_names, new_text = replace_similar_names(text, names_list)

st.subheader("Names replaced:")
for original, replaced in replaced_names:
    st.write(f"{original} -> {replaced}")

st.subheader("Text with replaced names:")
st.write(new_text)

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
