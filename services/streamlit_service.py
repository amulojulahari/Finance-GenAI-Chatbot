import io
import os

import pandas as pd
import streamlit
from PIL import Image

from config.configuration import configs
from constants import app_constants as ac
from services import file_service as fs
from services import operations_service as ops


def get_image_bytes(image_path):
    with Image.open(image_path) as img:
        extension = fs.get_file_extension(img)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=extension.upper())
        img_bytes = img_bytes.getvalue()
    return img_bytes


@streamlit.cache_data(show_spinner=configs['streamlit.spinner.messages.get_assistant_avatar'])
def get_assistant_avatar(tenant):
    image_path = get_assistant_icon_path(tenant)
    return get_image_bytes(image_path)


@streamlit.cache_data(show_spinner=configs['streamlit.spinner.messages.get_user_avatar'])
def get_user_avatar(tenant):
    image_path = os.path.join(ac.ROOT_PATH, 'resources', tenant, 'st_user.png')
    return get_image_bytes(image_path)


@streamlit.cache_data(show_spinner=configs['streamlit.spinner.messages.get_avatar_for_role'])
def get_avatar_for_role(role, tenant):
    return get_user_avatar(tenant) if role == 'user' else get_assistant_avatar(tenant)


def get_assistant_icon_path(tenant):
    return os.path.join(ac.ROOT_PATH, 'resources', tenant, 'st_assistant.png')


def get_selection_from_sidebar(st: streamlit, message, values):
    return st.sidebar.selectbox(message, values)


@streamlit.cache_data(show_spinner=configs['streamlit.spinner.messages.write_response'])
def write_response(st, response, file_type=None):
    if file_type == ac.FILE_TYPE_EXCEL:
        try:
            response = ops.parse_response(response)
            for part in response:
                if isinstance(part, dict):
                    if 'bar' in part:
                        data = part['bar']
                        print('Before:' + str(data))
                        df = ops.crate_dataframe_from_date(data)
                        print('After:' + str(data))
                        st.bar_chart(df)

                    if 'line' in part:
                        data = part['line']
                        df = ops.crate_dataframe_from_date(data)
                        st.line_chart(df)

                    if 'table' in part:
                        data = part['table']
                        df = pd.DataFrame(data['data'], columns=data['columns'])
                        st.table(df)
                else:
                    st.markdown(part)
        except Exception as e:
            print('Exception in write_response: ' + e)
            st.markdown(response)
    else:
        st.markdown(response)
