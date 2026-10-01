import re

THOUSANDS_SEPARATORS = re.compile("[\\s'\u2019\u00a0\u202f]")
CURRENCY_AND_DASHES = re.compile("(?i)chf|fr\\.?|\u20ac|\\.[-\u2013]+$|[-\u2013]+$")
DECIMAL_COMMA = ","


def parse_amount(raw: object) -> float | None:
    """Reads Swiss/French amounts such as 1'234.50, 1 234,50 or CHF 12.-."""
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int | float):
        return float(raw)
    if not isinstance(raw, str):
        return None
    text = CURRENCY_AND_DASHES.sub("", raw.strip())
    text = THOUSANDS_SEPARATORS.sub("", text).replace(DECIMAL_COMMA, ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
