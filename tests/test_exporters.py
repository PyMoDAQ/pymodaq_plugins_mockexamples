# -*- coding: utf-8 -*-
"""
Created the 04/11/2023

@author: Sebastien Weber
"""
import numpy as np
from pathlib import Path
import pytest

from pymodaq_data.h5modules.saving import H5SaverLowLevel
from pymodaq_data import data as data_mod
from pymodaq_data.h5modules.data_saving import DataSaverLoader, AxisSaverLoader

from pymodaq_data.h5modules import exporter as h5export
from pymodaq_data.h5modules.utils import register_exporter, register_exporters


def test_register_exporter_mock_examples():

    exporter_modules = register_exporter('pymodaq_plugins_mockexamples')
    assert len(exporter_modules) >= 1  # this is the base exporter module
    assert len(h5export.ExporterFactory.exporters_registry['txt']) >= 2
