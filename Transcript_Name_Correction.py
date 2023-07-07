import re
import requests
import PyPDF2
import docx
import nltk
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from io import BytesIO, StringIO
import streamlit as st
from PIL import Image

nltk.download('names')
nltk.download('punkt')

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def custom_replacement(match, most_similar_name):
    return f"{match.group(1)}\n{most_similar_name}"

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
            text = re.sub(fr'(\d\d:\d\d:\d\d,\d\d\d\s-->\s\d\d:\d\d:\d\d,\d\d\d\n)({full_name})',
                          lambda match: custom_replacement(match, most_similar_name), text)

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

# Load and display the banner image
banner_image = Image.open('banner.jpg')
st.image(banner_image, use_column_width=True)

st.title("Text Analysis App")

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
