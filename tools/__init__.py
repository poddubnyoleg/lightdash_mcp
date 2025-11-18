import importlib
import pkgutil

tool_registry = {}

for _, module_name, _ in pkgutil.iter_modules(__path__):
    if module_name != "base_tool":
        module = importlib.import_module(f".{module_name}", package=__name__)
        tool_name = module.TOOL_DEFINITION.name
        tool_registry[tool_name] = module
