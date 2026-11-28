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
# the names of the modules say nothing: what each one is, is the plugin and, for the user, the term assigned
ACTUATORS = {'M2': 'MockBeamBlock', 'M1': 'MockSampleChanger'}
# the value of each state is what the user configured on the bench (here the bench blocks above 0.5)
STATES = {NS + 'BeamBlocked': ('M2', 1.), NS + 'BeamOpen': ('M2', 0.),
          NS + 'BlankInBeam': ('M1', 0.), NS + 'SampleInBeam': ('M1', 1.)}


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
    actuators = []
    for name, plugin in ACTUATORS.items():
        actuator = creator.create_actuator(name, plugin, 'Simple')
        creator.set_actuator_type(actuator, plugin)
        creator.add_actuator(actuator)
        actuator.init_hardware_ui(True)
        actuators.append(actuator)
    detector = creator.create_detector('Spectro', DAQTypesEnum.DAQ1D)
    creator.set_detector_type(detector, DAQTypesEnum.DAQ1D, 'MockSpectro')
    creator.add_detector(detector)
    detector.init_hardware_ui(True)
    qtbot.waitUntil(lambda: detector.initialized_state and all(a.initialized_state for a in actuators), timeout=10000)
    dashboard.modules_manager.detectors_all = [detector]
    dashboard.modules_manager.actuators_all = actuators
    yield dashboard
    QtWidgets.QApplication.processEvents()
    dashboard.quit_fun()


@fixture
def extension(dashboard):
    win_ext, ext = create_extension(dashboard, SpectroConcepts, show_extension=False)
    ext.do_things_after_experiment_set('spectro experiment', False)
    yield ext
    ext.quit_fun()


def assign(extension, states):
    """Assign the term of the spectrometer and associate the values of the actuators with states"""
    manager = extension.ontology_manager
    manager.update_channels_from_dashboard()
    manager.probe()
    channel = next(c for c in manager.channels if c.module == 'Spectro')
    manager.assign(channel.key, NS + 'Spectrum')
    for state in states:
        actuator, value = STATES[state]
        manager.assign_state(actuator, value, state)


def test_the_spectro_ontology_is_given_to_the_manager(extension):
    assert extension.ontology_manager.source is not None
    assert NS + 'Transmittance' in extension.ontology_manager.terms


def test_nothing_can_be_measured_without_terms(extension):
    assert extension.show_what_is_possible().startswith('Nothing can be measured yet')


def test_the_state_without_value_is_named(extension):
    assign(extension, [s for s in STATES if s != NS + 'SampleInBeam'])
    text = extension.show_what_is_possible()
    assert text.startswith('Can measure: Dark spectrum, Reference spectrum')
    assert 'Sample spectrum needs a value of an actuator for: Sample in beam' in text


def test_the_protocol_measures_and_computes_whatever_the_names(extension, qtbot):
    assign(extension, list(STATES))
    text = extension.show_what_is_possible()
    assert text.startswith('Can measure: Dark spectrum, Reference spectrum, Sample spectrum')
    assert 'Then can compute: Transmittance, Absorbance' in text
    extension.run_protocol()
    qtbot.waitUntil(lambda: not extension._busy, timeout=30000)
    assert extension.settings['status'] == 'Computed: Transmittance, Absorbance'
    assert set(extension._results) == {NS + 'DarkSpectrum', NS + 'ReferenceSpectrum', NS + 'SampleSpectrum'}
    # the spectra are the ones of the states of the bench: dark level, lamp, lamp through the sample
    dark, reference, sample = (extension._results[NS + name].mean()
                               for name in ('DarkSpectrum', 'ReferenceSpectrum', 'SampleSpectrum'))
    assert dark < 200 < sample < reference
