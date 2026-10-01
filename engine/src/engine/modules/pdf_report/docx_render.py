from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docxtpl import DocxTemplate
from jinja2 import Environment, StrictUndefined, TemplateError, UndefinedError

from engine.core.errors import EngineError, OutputWriteError

DEFAULT_TEMPLATE_NAME = "rapport-par-defaut.docx"
FIX_TEMPLATE_HINT = (
    "Corrigez la balise dans le modèle Word ou ajoutez-la dans Paramètres → Rapport."
)


class ReportTemplateError(EngineError):
    pass


def render_report(template: Path | None, context: dict[str, Any], target: Path) -> None:
    if template is not None:
        _render(template, context, target, source=template)
        return
    with TemporaryDirectory(prefix="drawflow-docx-") as workdir:
        default = write_default_template(Path(workdir) / DEFAULT_TEMPLATE_NAME)
        _render(default, context, target, source=None)


def write_default_template(path: Path) -> Path:
    document = Document()
    document.add_heading("Rapport de plans", level=0)
    document.add_paragraph("Projet : {{ projet }} — Date : {{ date }} — {{ nb_plans }} plan(s)")
    document.add_paragraph("{%p for plan in plans %}")
    document.add_heading("{{ plan.fichier }} ({{ plan.pages }} page(s))", level=1)
    document.add_paragraph("{%p for champ in plan.liste_champs %}")
    document.add_paragraph("{{ champ.libelle }} : {{ champ.valeur }}")
    document.add_paragraph("{%p endfor %}")
    document.add_paragraph("Références : {{ plan.references }}")
    document.add_paragraph("{%p endfor %}")
    document.save(str(path))
    return path


def _render(template: Path, context: dict[str, Any], target: Path, source: Path | None) -> None:
    document = _open(template)
    try:
        document.render(context, jinja_env=Environment(undefined=StrictUndefined, autoescape=True))
    except UndefinedError as error:
        raise ReportTemplateError(
            f"Balise inconnue dans le modèle Word : {error.message}.",
            file=source,
            hint=FIX_TEMPLATE_HINT,
        ) from error
    except TemplateError as error:
        raise ReportTemplateError(
            f"Le modèle Word contient une balise mal écrite : {error.message}.",
            file=source,
            hint="Vérifiez les accolades {{ }} et {% %} du modèle.",
        ) from error
    _save(document, target)


def _open(template: Path) -> DocxTemplate:
    try:
        document = DocxTemplate(str(template))
        document.init_docx()
    except (OSError, BadZipFile, KeyError, ValueError, PackageNotFoundError) as error:
        raise ReportTemplateError(
            "Le modèle Word est illisible.",
            file=template,
            hint="Choisissez un fichier .docx valide.",
        ) from error
    return document


def _save(document: DocxTemplate, target: Path) -> None:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(target))
    except OSError as error:
        raise OutputWriteError(
            "Impossible d'enregistrer le rapport.",
            file=target,
            hint="Fermez le fichier s'il est ouvert dans Word et vérifiez le dossier de sortie.",
        ) from error
