import streamlit as st
from PIL import Image
import nltk
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document

# Load and display the banner image
banner_image = Image.open('banner.jpg')
st.image(banner_image, use_column_width=True)

st.title("Text Analysis App")

uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
    st.write(file_details)

    file_content = uploaded_file.getvalue()
    if uploaded_file.type == "application/pdf":
        pdfReader = PyPDF2.PdfFileReader(uploaded_file)
        num_pages = pdfReader.numPages
        st.write(f"Number of pages: {num_pages}")

        text = []
        for page in range(num_pages):
            pageObj = pdfReader.getPage(page)
            text.append(pageObj.extractText())

        all_text = "\n".join(text)
        st.write(all_text)

    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        
        all_text = "\n".join(text)
        st.write(all_text)

    elif uploaded_file.type == "text/html":
        soup = BeautifulSoup(uploaded_file, "html.parser")
        all_text = soup.get_text()
        st.write(all_text)

    else:
        all_text = uploaded_file.read()
        st.write(all_text)

    # Perform text analysis
    st.write("### Text Analysis")
    words = nltk.word_tokenize(all_text)
    num_words = len(words)
    st.write(f"Number of words: {num_words}")

    num_chars = len(all_text)
    st.write(f"Number of characters: {num_chars}")

    num_sentences = len(nltk.sent_tokenize(all_text))
    st.write(f"Number of sentences: {num_sentences}")

    avg_word_length = round(num_chars / num_words, 2)
    st.write(f"Average word length: {avg_word_length}")

    avg_sentence_length = round(num_words / num_sentences, 2)
    st.write(f"Average sentence length: {avg_sentence_length}")
