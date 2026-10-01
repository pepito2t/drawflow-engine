import unicodedata


def fold(text: str) -> str:
    """Accent- and case-insensitive form that keeps one character per input character."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return stripped.casefold() if len(stripped) == len(text) else text.casefold()
