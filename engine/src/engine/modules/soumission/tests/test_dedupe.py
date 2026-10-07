from pathlib import Path

from engine.modules.soumission.dedupe import Duplicate, deduplicate


def test_identical_contents_keep_the_first_file() -> None:
    first = Path("Lot A") / "offre.xlsx"
    copy = Path("Lot B") / "offre (copie).xlsx"
    other = Path("Lot B") / "autre.xlsx"

    result = deduplicate([(first, "1"), (copy, "1"), (other, "2")])

    assert result.unique == [first, other]
    assert result.duplicates == [Duplicate(path=copy, same_as=first)]


def test_nothing_to_deduplicate() -> None:
    assert deduplicate([]).unique == []
