import pytest
from pydantic import ValidationError

from engine.core.fields import KeyValue
from engine.modules.pdf_report.fields import extract_fields, find_references
from engine.modules.pdf_report.reader import TextLine
from engine.modules.pdf_report.settings import DEFAULT_FIELDS, PdfReportSettings


def line(text: str, top: float, x0: float = 0, x1: float = 200) -> TextLine:
    return TextLine(text=text, x0=x0, top=top, x1=x1, bottom=top + 8)


TITLE_BLOCK = [
    line("Projet : Tour B", 10),
    line("N° plan: F-102", 20),
    line("INDICE - C", 30),
    line("Echelle", 40),
    line("1:50", 50),
    line("Dessiné par TMBK", 60),
]


def test_values_follow_their_label_accent_and_case_insensitively() -> None:
    result = extract_fields(TITLE_BLOCK, DEFAULT_FIELDS)

    assert result.values["projet"] == "Tour B"
    assert result.values["numero_plan"] == "F-102"
    assert result.values["indice"] == "C"
    assert result.values["auteur"] == "TMBK"


def test_label_after_a_sharp_s_keeps_its_position() -> None:
    rules = [KeyValue(key="masse", value="Maße")]
    lines = [line("Straße 5, Größe L, Maße 3 x 4 m", 0)]

    assert extract_fields(lines, rules).values["masse"] == "3 x 4 m"


def test_value_on_the_next_line_below_the_label() -> None:
    assert extract_fields(TITLE_BLOCK, DEFAULT_FIELDS).values["echelle"] == "1:50"


def test_missing_fields_are_empty_and_listed() -> None:
    result = extract_fields(TITLE_BLOCK, DEFAULT_FIELDS)

    assert result.values["date"] == ""
    assert result.missing == ["date"]


def test_regex_rules_use_their_first_group() -> None:
    rules = [KeyValue(key="lot", value=r"re:Lot\s+(\d+)")]

    assert extract_fields([line("Façade Lot 4 nord", 0)], rules).values["lot"] == "4"


def test_references_are_collected_sorted_and_unique() -> None:
    lines = [line("Voir EQ-40 et P-1200", 0), line("P-1200 / F-80A", 10)]

    assert find_references(lines, PdfReportSettings().reference_pattern) == [
        "EQ-40",
        "F-80A",
        "P-1200",
    ]


@pytest.mark.parametrize(
    "fields",
    [
        [{"key": "Projet", "value": "Projet"}],
        [{"key": "lot", "value": "re:(unclosed"}],
    ],
)
def test_invalid_rules_are_rejected(fields: list[dict[str, str]]) -> None:
    with pytest.raises(ValidationError):
        PdfReportSettings.model_validate({"fields": fields})


def test_invalid_reference_pattern_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PdfReportSettings(reference_pattern="[A-Z")
