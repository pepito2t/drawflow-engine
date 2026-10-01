from pathlib import Path

from engine.modules.soumission.dedupe import Duplicate, deduplicate


def test_identical_contents_keep_the_first_file(tmp_path: Path) -> None:
    first = tmp_path / "Lot A" / "offre.xlsx"
    copy = tmp_path / "Lot B" / "offre (copie).xlsx"
    other = tmp_path / "Lot B" / "autre.xlsx"
    for path, content in ((first, b"1"), (copy, b"1"), (other, b"2")):
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(content)

    result = deduplicate([first, copy, other])

    assert result.unique == [first, other]
    assert result.duplicates == [Duplicate(path=copy, same_as=first)]


def test_digest_is_injectable() -> None:
    paths = [Path("a"), Path("b")]

    assert deduplicate(paths, digest=lambda _: "same").unique == [Path("a")]
