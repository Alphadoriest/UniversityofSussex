import re
import requests
import PyPDF2
import docx
import nltk
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from io import BytesIO, StringIO
import streamlit as st

nltk.download('names')
nltk.download('punkt')

# Replace the URL below with the image URL of The University of Sussex
IMAGE_URL = "https://www.example.com/sussex_university_logo.jpg"

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

def read_pdf(file):
    pdf_reader = PyPDF2.PdfFileReader(file)
    text = ''
    for page_num in range(pdf_reader.numPages):
        text += pdf_reader.getPage(page_num).extractText()
    return text

def read_docx(file):
    doc = docx.Document(file)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text
    return text

def read_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text(separator='\n')
    return text

def extract_names(text):
    words = nltk.word_tokenize(text)
    names = set()
    for word in words:
        if word.istitle() and word.lower() not in nltk.corpus.names.words('male.txt') + nltk.corpus.names.words('female.txt'):
            names.add(word)
    return ', '.join(names)

# Display the banner image
st.image(https://assetbank-eu-west-1-thumbnails.s3.eu-west-1.amazonaws.com/sussex_5bfc7c294c3a67a87231cebbd6fb9162/d5e/4zQ0U1q9SKoQJtX67oPyIYpqA0y30eOo.jpg?response-content-disposition=inline%3B%20filename%3D%22abt_738888560706388056MTQ3Ng.jpg%22%3B%20filename%2A%3DUTF-8%27%27abt%255F738888560706388056MTQ3Ng%252Ejpg&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20230707T223454Z&X-Amz-SignedHeaders=host&X-Amz-Expires=900&X-Amz-Credential=AKIAJAFNSNM4PNBWWYLQ%2F20230707%2Feu-west-1%2Fs3%2Faws4_request&X-Amz-Signature=7c1911cb3a39ca420253db742631a162e33ed2aaef4646efb62d8286bad644dc, use_column_width=True)

st.title("Graduation Transcript Name Correction")

names_input = st.text_input("Enter all names from a Ceremony In-Person List (separated by commas):")
text_input = st.text_area("Enter Subtitles/Transcript text:")

names_file = st.file_uploader("Upload Ceremony In-Person List:", type=['pdf', 'docx', 'txt', 'html', 'vtt'])
text_file = st.file_uploader("Upload Subtitles/Transcript file:", type=['pdf', 'docx', 'txt', 'html', 'vtt'])

if names_file:
    if names_file.type == 'application/pdf':
        names_text = read_pdf(names_file)
    elif names_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        names_text = read_docx(names_file)
    elif names_file.type in ['text/plain', 'text/html', 'text/vtt']:
        names_text = names_file.getvalue().decode('utf-8')

    names_input = extract_names(names_text)

if text_file:
    if text_file.type == 'application/pdf':
        text_input = read_pdf(text_file)
    elif text_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        text_input = read_docx(text_file)
    elif text_file.type in ['text/plain', 'text/html', 'text/vtt']:
        text_input = text_file.getvalue().decode('utf-8')

if st.button("Submit"):
    names_list = [name.strip() for name in names_input.split(',')]
    replaced_names, new_text = replace_similar_names(text_input, names_list)

    st.write("Names replaced:")
    for original, replaced in replaced_names:
        st.write(f"{original} -> {replaced}")

    st.write("\nText with replaced names:")
    st.write(new_text)
