import importlib
import json
import os

import pandas as pd
import streamlit as st
from langchain_community.document_loaders.merge import MergedDataLoader
from langchain_community.document_loaders.directory import DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.configuration import configs
from constants import app_constants as ac

from services import common_service as cs
from services.decorators import timing


@st.cache_resource(show_spinner=configs['streamlit.spinner.messages.get_processed_data_from_text'])
def get_processed_data_from_text(text):
    text_splitter = get_text_splitter()
    chunks = text_splitter.split_text(text)
    return FAISS.from_texts(chunks, embedding=cs.get_embeddings())


@st.cache_resource(show_spinner=configs['streamlit.spinner.messages.get_processed_data_from_loader'])
def get_processed_data_from_loader(_merged_data_loader: MergedDataLoader):
    documents = _merged_data_loader.load()
    text_splitter = get_text_splitter()
    split_docs = text_splitter.split_documents(documents)
    return FAISS.from_documents(split_docs, embedding=cs.get_embeddings())


def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )


def parse_response(response):
    parts = []
    json_start = response.find("{")
    json_end = response.rfind("}") + 1
    if json_start != -1 and json_end != 0:
        parts.append(response[:json_start])
        json_string = response[json_start:json_end]
        parts.append(json.loads(json_string))
        parts.append(response[json_end:])
    else:
        parts = [response]
    return parts


def crate_dataframe_from_date(data):
    if isinstance(data['data'][0], list):
        data['columns'] = [item[0] for item in data['data']]
        data['data'] = [item[1] for item in data['data']]
    df = pd.DataFrame(data)
    df.set_index('columns', inplace=True)
    return df


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_prompt_result_from_context'])
@timing(print_args=False)
def get_prompt_result_from_context(combined_prompt, _chain=None, _agent=None):
    answer = None
    if _chain:
        result = _chain.invoke({'question': str(combined_prompt),
                                'chat_history': [(message['role'], message['content']) for message in
                                                 st.session_state.messages]})
        print(f'Result: {json.dumps(result)}')
        answer = result['answer']
    elif _agent:
        result = _agent.invoke(str(combined_prompt))
        print(f'Result: {json.dumps(result)}')
        answer = result['output']
    print(f'Prompt response from LLM: {str(answer)}')
    return answer


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_prompt_result'])
def get_prompt_result(_llm, prompt):
    return _llm.invoke(prompt).content