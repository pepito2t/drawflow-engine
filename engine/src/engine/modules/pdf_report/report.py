from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from engine.core.fields import KeyValue
from engine.modules.pdf_report.settings import REGEX_PREFIX

REPORT_DATE_FORMAT = "%d.%m.%Y"
REFERENCES_SEPARATOR = ", "


@dataclass(frozen=True)
class PlanData:
    file_name: str
    pages: int
    fields: dict[str, str]
    references: list[str] = field(default_factory=list)


def build_context(
    plans: Sequence[PlanData], rules: Sequence[KeyValue], project: str, moment: datetime
) -> dict[str, Any]:
    """Word template variables; plan fields are exposed directly (plan.indice) and as a list."""
    return {
        "projet": project,
        "date": moment.strftime(REPORT_DATE_FORMAT),
        "nb_plans": len(plans),
        "plans": [_plan_context(plan, rules) for plan in plans],
    }


def _plan_context(plan: PlanData, rules: Sequence[KeyValue]) -> dict[str, Any]:
    return {
        **plan.fields,
        "fichier": plan.file_name,
        "pages": plan.pages,
        "references": REFERENCES_SEPARATOR.join(plan.references),
        "liste_references": plan.references,
        "champs": plan.fields,
        "liste_champs": [
            {"libelle": _label(rule), "valeur": plan.fields.get(rule.key, "")} for rule in rules
        ],
    }


def _label(rule: KeyValue) -> str:
    return rule.key if rule.value.startswith(REGEX_PREFIX) else rule.value
