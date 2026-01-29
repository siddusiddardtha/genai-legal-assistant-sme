from langdetect import detect, DetectorFactory

# Fix randomness issue in langdetect
DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    """
    Detects language of the given text.
    Returns: 'English', 'Hindi', or 'Unknown'
    """
    try:
        lang_code = detect(text)

        if lang_code == "en":
            return "English"
        elif lang_code == "hi":
            return "Hindi"
        else:
            return "Unknown"

    except Exception:
        return "Unknown"
