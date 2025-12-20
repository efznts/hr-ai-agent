
"""
Translation module using GigaChat.
"""
from langdetect import detect
from src.api.gigachat import gigachat_client


def detect_language(text: str) -> str:
    """Detect text language."""
    try:
        return detect(text)
    except:
        return "en"


def translate_if_needed(text: str, source_lang: str = None) -> str:
    """Translate text to Russian if not already in Russian."""
    if not text:
        return ""
    
    # Detect language if not provided
    if not source_lang:
        source_lang = detect_language(text)
    
    # Skip if already Russian
    if source_lang == "ru":
        return text
    
    # Translate using GigaChat
    try:
        translated = gigachat_client.translate_to_russian(text)
        return translated if translated else text
    except Exception as e:
        print(f"Translation error: {e}")
        return text
