import pytest

from engine.modules.soumission.numbers import parse_amount


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (12, 12.0),
        (3.5, 3.5),
        ("1'234.50", 1234.5),
        ("1\u2019234.50", 1234.5),
        ("1 234,50", 1234.5),
        ("1\u202f234,50", 1234.5),
        ("CHF 12.-", 12.0),
        ("12.\u2013", 12.0),
        ("Fr. 45", 45.0),
        ("-3", -3.0),
    ],
)
def test_parses_swiss_and_french_amounts(raw: object, expected: float) -> None:
    assert parse_amount(raw) == expected


@pytest.mark.parametrize("raw", ["", "forfait", None, True])
def test_returns_none_for_non_amounts(raw: object) -> None:
    assert parse_amount(raw) is None
