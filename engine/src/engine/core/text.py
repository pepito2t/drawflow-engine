import unicodedata


def fold(text: str) -> str:
    """Accent- and case-insensitive form that keeps one character per input character."""
    lowered = text.casefold()
    if len(lowered) != len(text):
        # "ß" casefolds to "ss": lower() keeps a position for every input character.
        lowered = text.lower()
    stripped = _without_accents(lowered)
    return stripped if len(stripped) == len(text) else lowered


def _without_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))
