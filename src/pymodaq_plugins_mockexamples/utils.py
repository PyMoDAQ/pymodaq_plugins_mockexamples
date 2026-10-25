# -*- coding: utf-8 -*-
"""
Created the 31/08/2023

@author: Sebastien Weber
"""
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

