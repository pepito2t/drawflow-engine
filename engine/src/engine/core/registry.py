import importlib
import pkgutil
from functools import cache
from typing import Any

import engine.modules as modules_package
from engine.core.contract import EngineModule
from engine.core.errors import ModuleContractError, UnknownModuleError
from engine.core.messages import t

MODULE_ATTRIBUTE = "MODULE"
AnyModule = EngineModule[Any]


def discover_modules() -> dict[str, AnyModule]:
    return dict(_discovered())


@cache
def _discovered() -> tuple[tuple[str, AnyModule], ...]:
    found: dict[str, AnyModule] = {}
    prefix = f"{modules_package.__name__}."
    for info in pkgutil.iter_modules(modules_package.__path__, prefix=prefix):
        if not info.ispkg:
            continue
        module = _load_module(info.name)
        if module.manifest.id in found:
            raise ModuleContractError(t("registry.duplicate_id", module_id=module.manifest.id))
        found[module.manifest.id] = module
    return tuple(sorted(found.items(), key=lambda item: (item[1].manifest.order, item[0])))


def get_module(module_id: str) -> AnyModule:
    modules = discover_modules()
    if module_id not in modules:
        available = ", ".join(sorted(modules)) or t("registry.none")
        raise UnknownModuleError(
            t("registry.unknown", module_id=module_id),
            hint=t("registry.unknown_hint", available=available),
        )
    return modules[module_id]


def _load_module(package_name: str) -> AnyModule:
    package = importlib.import_module(package_name)
    module = getattr(package, MODULE_ATTRIBUTE, None)
    if not isinstance(module, EngineModule):
        raise ModuleContractError(
            t("registry.invalid_attribute", package=package_name, attribute=MODULE_ATTRIBUTE)
        )
    return module
