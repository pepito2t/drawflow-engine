from pathlib import Path

from engine.core.errors import OutputWriteError
from engine.core.naming import unique_output_path


class FileSystemGreetingWriter:
    def write_text(self, folder: Path, file_name: str, content: str) -> Path:
        target = folder / file_name
        try:
            folder.mkdir(parents=True, exist_ok=True)
            target = unique_output_path(folder, file_name)
            target.write_text(content, encoding="utf-8")
        except OSError as error:
            raise OutputWriteError(
                "Impossible d'écrire le fichier de sortie.",
                file=target,
                hint="Vérifiez que le dossier de sortie est accessible en écriture.",
            ) from error
        return target
