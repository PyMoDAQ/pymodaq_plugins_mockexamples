"""Test of the demo extension working on the terms of the channels, with the simulated spectrometers"""
import pytest
import qt_themes
from pytest import fixture
from qtpy import QtWidgets

pytest.importorskip('pymodaq_plugins_mock', reason='The mock instruments of PyMoDAQ are needed')
pytest.importorskip('pymodaq_ontology', reason='The ontology manager is needed')

from pymodaq_utils.config import GlobalConfig

from pymodaq.control_modules.enums import DAQTypesEnum
from pymodaq.dashboard import create_load_dashboard
from pymodaq.utils.custom_ext import CustomExt
from pymodaq.utils.gui_utils.loader_utils import create_extension

from pymodaq_ontology import manager as manager_module

from pymodaq_plugins_mockexamples.extensions import spectro_concepts
from pymodaq_plugins_mockexamples.extensions.spectro_concepts import SpectroConcepts

NS = 'http://example.org/mockexamples#'
# the names of the modules say nothing: what each one measures is the plugin and, for the user, the term assigned
MODULES = {'S1': 'MockSpectroSample', 'S2': 'MockSpectroDark', 'S3': 'MockSpectroReference'}
TERMS = {'S1': NS + 'SampleSpectrum', 'S2': NS + 'DarkSpectrum', 'S3': NS + 'ReferenceSpectrum'}


def test_is_a_dashboard_extension():
    assert spectro_concepts.EXTENSION_NAME
    assert spectro_concepts.CLASS_NAME == SpectroConcepts.__name__
    assert issubclass(SpectroConcepts, CustomExt)
    assert spectro_concepts.TERMS_FILE.is_file()


@fixture
def dashboard(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr(manager_module, 'get_set_config_dir', lambda name, user=False: tmp_path / name)
    (tmp_path / 'ontology').mkdir()
    config = GlobalConfig()
    qt_themes.set_theme(theme=config('gui', 'style', 'theme')[0], style=config('gui', 'style', 'style')[0])
    shared_ui, dashboard = create_load_dashboard(show_dashboard=False)
    qtbot.addWidget(shared_ui.parent)
    qtbot.addWidget(dashboard.tree)

    creator = dashboard.module_creator
    detectors = []
    for name, plugin in MODULES.items():
        detector = creator.create_detector(name, DAQTypesEnum.DAQ1D)
        creator.set_detector_type(detector, DAQTypesEnum.DAQ1D, plugin)
        creator.add_detector(detector)
        detector.init_hardware_ui(True)
        detectors.append(detector)
    qtbot.waitUntil(lambda: all(d.initialized_state for d in detectors), timeout=10000)
    dashboard.modules_manager.detectors_all = detectors
    yield dashboard
    QtWidgets.QApplication.processEvents()
    dashboard.quit_fun()


@fixture
def extension(dashboard):
    win_ext, ext = create_extension(dashboard, SpectroConcepts, show_extension=False)
    ext.do_things_after_experiment_set('spectro experiment', False)
    yield ext
    ext.quit_fun()


def assign(extension, modules):
    manager = extension.ontology_manager
    manager.probe()
    for module in modules:
        channel = next(c for c in manager.channels if c.module == module)
        manager.assign(channel.key, TERMS[module])


def test_the_spectro_ontology_is_given_to_the_manager(extension):
    assert extension.ontology_manager.source is not None
    assert NS + 'Transmittance' in extension.ontology_manager.terms


def test_nothing_to_compute_without_terms(extension):
    assert extension.show_what_is_possible().startswith('Nothing can be computed yet')


def test_the_missing_term_is_named(extension):
    assign(extension, ['S1', 'S3'])  # sample and reference, no dark
    text = extension.show_what_is_possible()
    assert text.startswith('Nothing can be computed yet')
    assert 'Transmittance needs: Dark spectrum' in text


def test_transmittance_and_absorbance_are_computed_whatever_the_names(extension, qtbot):
    assign(extension, ['S1', 'S2', 'S3'])
    assert extension.show_what_is_possible().startswith('Can compute: Transmittance, Absorbance')
    extension.grab_and_compute()
    qtbot.waitUntil(lambda: not extension._busy, timeout=15000)
    assert extension.settings['status'].startswith('Can compute: Transmittance, Absorbance')
