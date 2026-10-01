import importlib
import pkgutil
from typing import Any

import engine.modules as modules_package
from engine.core.contract import EngineModule
from engine.core.errors import ModuleContractError, UnknownModuleError

MODULE_ATTRIBUTE = "MODULE"
AnyModule = EngineModule[Any]


def discover_modules() -> dict[str, AnyModule]:
    found: dict[str, AnyModule] = {}
    prefix = f"{modules_package.__name__}."
    for info in pkgutil.iter_modules(modules_package.__path__, prefix=prefix):
        if not info.ispkg:
            continue
        module = _load_module(info.name)
        if module.manifest.id in found:
            raise ModuleContractError(
                f"Deux modules utilisent l'identifiant « {module.manifest.id} »."
            )
        found[module.manifest.id] = module
    return dict(sorted(found.items(), key=lambda item: (item[1].manifest.order, item[0])))


def get_module(module_id: str) -> AnyModule:
    modules = discover_modules()
    if module_id not in modules:
        available = ", ".join(sorted(modules)) or "aucun"
        raise UnknownModuleError(
            f"La fonctionnalité « {module_id} » n'existe pas.",
            hint=f"Fonctionnalités disponibles : {available}.",
        )
    return modules[module_id]


def _load_module(package_name: str) -> AnyModule:
    package = importlib.import_module(package_name)
    module = getattr(package, MODULE_ATTRIBUTE, None)
    if not isinstance(module, EngineModule):
        raise ModuleContractError(
            f"Le module « {package_name} » n'expose pas d'attribut {MODULE_ATTRIBUTE} valide."
        )
    return module
