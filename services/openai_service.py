from google import genai
from config.configuration import configs


def get_gemini_client():
    api_key = configs["openai.key"]

    if not api_key:
        return None

    return genai.Client(api_key=api_key)