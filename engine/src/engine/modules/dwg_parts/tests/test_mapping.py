from pathlib import Path

import pytest
from pydantic import ValidationError

from engine.core.fields import KeyValue
from engine.modules.dwg_parts.mapping import map_parts
from engine.modules.dwg_parts.reader import RawPart
from engine.modules.dwg_parts.settings import DwgPartsSettings

SOURCE = Path("plan.dwg")


def part(block: str, count: int = 1, **attributes: str) -> RawPart:
    return RawPart(block=block, attributes=attributes, count=count, layout="Model", source=SOURCE)


def settings(**overrides: object) -> DwgPartsSettings:
    base: dict[str, object] = {
        "columns": [KeyValue(key="Réf", value="REF"), KeyValue(key="Long.", value="LONGUEUR")],
        "include_block_name": False,
    }
    return DwgPartsSettings.model_validate({**base, **overrides})


def test_maps_attributes_to_columns_in_order() -> None:
    outcome = map_parts([part("PANNEAU", REF="P-1", LONGUEUR="1200")], settings())

    assert outcome.headers == ("Réf", "Long.")
    assert outcome.parts[0].values == ("P-1", "1200")


def test_block_column_comes_first_when_enabled() -> None:
    outcome = map_parts([part("PANNEAU", REF="P-1")], settings(include_block_name=True))

    assert outcome.headers[0] == "Bloc"
    assert outcome.parts[0].values[0] == "PANNEAU"


def test_block_patterns_filter_case_insensitively() -> None:
    parts = [part("Panneau_A", REF="1"), part("EQUERRE", REF="2"), part("COTE", REF="3")]

    outcome = map_parts(parts, settings(included_blocks="PANNEAU*; equerre"))

    assert [mapped.values[0] for mapped in outcome.parts] == ["1", "2"]


def test_missing_attributes_are_empty_and_reported_once_per_tag() -> None:
    outcome = map_parts([part("A", REF="1"), part("B", REF="2")], settings())

    assert outcome.parts[0].values == ("1", "")
    assert outcome.warnings == ["Attribut « LONGUEUR » absent sur 2 blocs (cellule laissée vide)."]


def test_quantity_attribute_and_minsert_count_multiply() -> None:
    outcome = map_parts([part("A", count=2, REF="1", LONGUEUR="5", QTE="3,5")], settings())

    assert outcome.parts[0].quantity == 7.0


def test_unreadable_quantity_counts_one_and_warns() -> None:
    outcome = map_parts([part("A", REF="1", LONGUEUR="5", QTE="beaucoup")], settings())

    assert outcome.parts[0].quantity == 1.0
    assert "illisible" in outcome.warnings[-1]


def test_tags_are_normalized_to_upper_case() -> None:
    normalized = settings(columns=[{"key": " Réf ", "value": " ref "}], quantity_attribute=" qte ")

    assert normalized.columns == [KeyValue(key="Réf", value="REF")]
    assert normalized.quantity_attribute == "QTE"


def test_at_least_one_column_is_required() -> None:
    with pytest.raises(ValidationError):
        settings(columns=[])


def test_mapping_schema_exposes_ui_labels() -> None:
    columns = DwgPartsSettings.model_json_schema()["properties"]["columns"]

    assert columns["x-ui"] == "mapping"
    assert columns["x-ui-key-label"] == "Colonne"
    assert columns["x-ui-value-label"] == "Attribut du bloc"
