# -*- coding: utf-8 -*-
"""
Created the 31/08/2023

@author: Sebastien Weber
"""
import functools
import shutil
from pathlib import Path

from pymodaq_utils.config import BaseConfig, USER


class Config(BaseConfig):
    """Main class to deal with configuration values for this plugin"""
    config_template_path = Path(__file__).parent.joinpath('resources/config_template.toml')
    config_name = f"config_{__package__.split('pymodaq_plugins_')[1]}"


def copy_experiments(config: Config) -> list[Path]:
    """Copy the experiment files of the resources folder in the experiments folder of PyMoDAQ

    A file already there is never overwritten, so the changes of the user are kept. Returns the copied files.
    """
    if not config('copy_experiments'):
        return []
    from pymodaq.utils.config import get_set_experiment_path
    destination = get_set_experiment_path()
    copied = []
    for source in sorted(Path(__file__).parent.joinpath('resources').glob('*.xml')):
        target = destination.joinpath(source.name)
        if not target.exists():
            shutil.copyfile(source, target)
            copied.append(target)
    return copied


def report_errors(method):
    """Decorator for the methods of a plugin that call a driver: show the error in the status bar of the module

    PyMoDAQ logs the exception raised by a plugin method but shows nothing in the user interface, so without this the
    user sees no sign that a move was refused or a reading failed. The status is emitted (it also reaches the log),
    then the exception is raised again so PyMoDAQ and the tests still see it.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            from pymodaq.control_modules.thread_commands import ThreadStatus
            from pymodaq_utils.utils import ThreadCommand
            self.emit_status(ThreadCommand(ThreadStatus.UPDATE_STATUS, f'{method.__name__}: {e}'))
            raise
    return wrapper
