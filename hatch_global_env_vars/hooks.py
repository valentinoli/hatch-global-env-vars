from hatchling.plugin import hookimpl

from .plugin import GlobalEnvVarsCollector


@hookimpl
def hatch_register_environment_collector():
    return GlobalEnvVarsCollector
