import re
from difflib import SequenceMatcher
import streamlit as st

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def replace_similar_names(text, names_list):
    # ... (same as before)

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
