import pytest

from engine.core.text import fold


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Échelle", "echelle"),
        ("DESSINÉ PAR", "dessine par"),
        ("Straße", "straße"),
        ("Größe : 12", "große : 12"),
    ],
)
def test_fold_ignores_case_and_accents_without_changing_the_length(
    text: str, expected: str
) -> None:
    assert fold(text) == expected
    assert len(fold(text)) == len(text)
