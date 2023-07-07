import re
from difflib import SequenceMatcher
import streamlit as st

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def replace_similar_names(text, names_list):
    full_name_pattern = re.compile(r'\b(?:\w+(?:\s+\w+){1,4})\b')
    full_names_in_text = full_name_pattern.findall(text)
    replaced_names = []

    for full_name in full_names_in_text:
        max_similarity = 0
        most_similar_name = None
        for name in names_list:
            sim = similarity(full_name, name)
            if sim > max_similarity:
                max_similarity = sim
                most_similar_name = name

        if max_similarity >= 0.8:  # Adjust the similarity threshold as needed
            replaced_names.append((full_name, most_similar_name))
            text = re.sub(fr'(\d\d:\d\d:\d\d,\d\d\d\s-->\s\d\d:\d\d:\d\d,\d\d\d\n)({full_name})', fr'\1{most_similar_name}\n', text)

    return replaced_names, text

st.title("Name Replacer")

names_input = st.text_input("Enter names to match (separated by commas):")
text_input = st.text_area("Enter text:")

if st.button("Submit"):
    names_list = [name.strip() for name in names_input.split(',')]
    replaced_names, new_text = replace_similar_names(text_input, names_list)

    st.write("Names replaced:")
    for original, replaced in replaced_names:
        st.write(f"{original} -> {replaced}")

    st.write("\nText with replaced names:")
    st.write(new_text)
