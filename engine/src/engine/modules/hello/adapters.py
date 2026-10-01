from pathlib import Path

from engine.core.errors import OutputWriteError


class FileSystemGreetingWriter:
    def write_text(self, path: Path, content: str) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError as error:
            raise OutputWriteError(
                "Impossible d'écrire le fichier de sortie.",
                file=path,
                hint="Vérifiez que le dossier de sortie est accessible en écriture.",
            ) from error
