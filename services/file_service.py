import os
import tempfile

import pytesseract
import streamlit as st
from PyPDF2 import PdfReader
from langchain_community.document_loaders.unstructured import UnstructuredFileLoader
from pdf2image import convert_from_path
from streamlit.runtime.uploaded_file_manager import UploadedFile
from unstructured.cleaners.core import clean_extra_whitespace

from config.configuration import configs
from services.decorators import timing


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_files_text'])
def get_files_text(files):
    return [get_file_text(file) for file in files]


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_file_text'])
@timing(print_args=True)
def get_file_text(file):
    text, file_extension, is_unstructured_loader_active = '', get_file_extension(file), configs['files.unstructuredLoader.active']
    print(f'file_extension is {file_extension}')
    if is_unstructured_loader_active and file_extension in configs['files.unstructuredLoader.extensions']:
        text = get_file_text_with_unstructured_loader(file)
    elif file_extension == 'pdf':
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
        if not text:
            if is_unstructured_loader_active:
                text = get_file_text_with_unstructured_loader(file.read())
            else:
                text = get_file_text_with_ocr(file)
    cleaned_text = "\n".join(line for line in text.splitlines() if line.strip())
    return cleaned_text


def get_file_text_with_ocr(file):
    pages = convert_from_path(get_temp_file(file))
    texts = ''
    for image in pages:
        texts += pytesseract.image_to_string(image, lang='eng')
    return texts


def get_file_text_with_unstructured_loader(file):
    return UnstructuredFileLoader(get_temp_file(file), post_processors=[clean_extra_whitespace]).load()[0].page_content


def get_temp_file(file):
    if isinstance(file, UploadedFile):
        temp_dir = tempfile.mkdtemp()
        temp_file = f"{temp_dir}/temp_{file.name}"
        with open(temp_file, "wb") as f:
            f.write(file.getbuffer())
        return temp_file
    return file


def get_file_extension(file):
    if isinstance(file, UploadedFile):
        filename = file.name
    else:
        filename = file.filename
    _, extension = os.path.splitext(filename)
    return extension.lower().lstrip('.')
