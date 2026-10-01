from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings

DEFAULT_FILE_NAME_TEMPLATE = "{type}_{date}-{heure}"


class HelloSettings(ModuleSettings):
    file_name_template: FileNameTemplate = file_name_template_field(DEFAULT_FILE_NAME_TEMPLATE)
