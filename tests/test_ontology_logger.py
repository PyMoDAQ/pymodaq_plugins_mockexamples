"""Tests of the demo extension annotating the saved data with the terms of an ontology"""
import pytest
import qt_themes
from pytest import fixture
from qtpy import QtWidgets

pytest.importorskip('pymodaq_plugins_mock', reason='The mock instruments of PyMoDAQ are needed')
pytest.importorskip('pymodaq_ontology', reason='The ontology manager is needed')

from pymodaq_utils.config import GlobalConfig

from pymodaq.control_modules.enums import DAQTypesEnum
from pymodaq.dashboard import create_load_dashboard
from pymodaq.extensions.daq_logger.daq_logger import DAQLogger
from pymodaq.utils.gui_utils.loader_utils import create_extension

from pymodaq_ontology import manager as manager_module

from pymodaq_plugins_mockexamples.extensions import ontology_logger
from pymodaq_plugins_mockexamples.extensions.ontology_logger import OntologyLogger

PHOTODIODE = 'http://example.org/mockexamples#Photodiode'


def test_is_a_dashboard_extension():
    assert ontology_logger.EXTENSION_NAME
    assert ontology_logger.CLASS_NAME == OntologyLogger.__name__
    assert issubclass(OntologyLogger, DAQLogger)
    assert ontology_logger.TERMS_FILE.is_file()


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
    detector = creator.create_detector('Det', DAQTypesEnum.DAQ0D)
    creator.set_detector_type(detector, DAQTypesEnum.DAQ0D, 'Mock')
    creator.add_detector(detector)
    detector.init_hardware_ui(True)
    qtbot.waitUntil(lambda: detector.initialized_state, timeout=10000)
    dashboard.modules_manager.detectors_all = [detector]
    yield dashboard
    QtWidgets.QApplication.processEvents()
    dashboard.quit_fun()


@fixture
def extension(dashboard):
    win_ext, ext = create_extension(dashboard, OntologyLogger, show_extension=False)
    ext.do_things_after_experiment_set('mock experiment', False)
    yield ext
    ext.quit_fun()


def test_the_basic_ontology_is_given_to_the_manager(extension):
    manager = extension.ontology_manager
    assert manager is not None
    assert PHOTODIODE in manager.terms


def test_the_saved_data_carry_the_assigned_term(extension, qtbot, tmp_path):
    manager = extension.ontology_manager
    manager.probe()
    channels = [c for c in manager.channels if c.module == 'Det']
    assert channels
    manager.assign(channels[0].key, PHOTODIODE)  # only the first channel of the mock detector

    extension.h5_manager.get_h5saver().settings['base_path'] = str(tmp_path)  # not in the user's data folder
    extension.modules_manager.selected_detectors_name = ['Det']  # the logger saves the selected detectors
    extension.logging.start()
    extension.modules_manager.detectors[0].snap()
    qtbot.waitUntil(lambda: extension.status_manager.n_saved >= 1, timeout=15000)
    extension.logging.stop('test')
    qtbot.waitUntil(lambda: extension.settings['saver_worker', 'worker_tasks'] == 0, timeout=15000)

    h5saver = extension.h5_manager.h5saver
    nodes = [n for n in h5saver.walk_nodes('/') if 'semantic_iri' in n.attrs]
    assert nodes
    iris = nodes[0].attrs['semantic_iri']
    assert PHOTODIODE in ([iris] if isinstance(iris, str) else list(iris))
