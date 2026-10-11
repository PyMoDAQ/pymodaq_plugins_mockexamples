"""Tests of the reference extension: it moves a mock actuator, grabs a mock detector, shows and saves the data"""
import pytest
import qt_themes
from pytest import fixture
from qtpy import QtWidgets

pytest.importorskip('pymodaq_plugins_mock', reason='The mock instruments of PyMoDAQ are needed')

from pymodaq_utils.config import GlobalConfig

from pymodaq.control_modules.enums import DAQTypesEnum
from pymodaq.dashboard import create_load_dashboard
from pymodaq.utils.custom_ext import CustomExt
from pymodaq.utils.gui_utils.loader_utils import create_extension

from pymodaq_plugins_mockexamples.extensions import move_and_grab
from pymodaq_plugins_mockexamples.extensions.move_and_grab import MoveAndGrab


def test_is_a_dashboard_extension():
    assert move_and_grab.EXTENSION_NAME
    assert move_and_grab.CLASS_NAME == MoveAndGrab.__name__
    assert issubclass(MoveAndGrab, CustomExt)


@fixture
def extension(qtbot):
    """The extension, running in a Dashboard with an initialized mock actuator and a mock 0D detector"""
    config = GlobalConfig()
    qt_themes.set_theme(theme=config('gui', 'style', 'theme')[0], style=config('gui', 'style', 'style')[0])
    shared_ui, dashboard = create_load_dashboard(show_dashboard=False)
    qtbot.addWidget(shared_ui.parent)
    qtbot.addWidget(dashboard.tree)

    creator = dashboard.module_creator
    actuator = creator.create_actuator('Move', 'Mock', None)
    creator.set_actuator_type(actuator, 'Mock')
    creator.add_actuator(actuator)
    detector = creator.create_detector('Det', DAQTypesEnum.DAQ0D)
    creator.set_detector_type(detector, DAQTypesEnum.DAQ0D, 'Mock')
    creator.add_detector(detector)
    for module in (actuator, detector):
        module.init_hardware_ui(True)
    qtbot.waitUntil(lambda: actuator.initialized_state and detector.initialized_state, timeout=10000)
    dashboard.modules_manager.actuators_all = [actuator]
    dashboard.modules_manager.detectors_all = [detector]

    win_ext, ext = create_extension(dashboard, MoveAndGrab, show_extension=False)
    ext.do_things_after_experiment_set('mock experiment', False)  # what the Dashboard does once an experiment is set
    yield ext, actuator
    ext.quit_fun()
    QtWidgets.QApplication.processEvents()
    dashboard.quit_fun()


def test_lists_the_instruments_of_the_dashboard(extension):
    ext, _ = extension
    assert ext.settings['actuator'] == 'Move'
    assert ext.settings['detector'] == 'Det'


def test_move_and_grab(extension, qtbot):
    ext, actuator = extension
    ext.settings['target'] = 5.
    ext.move_and_grab()
    assert ext._busy and not ext.is_action_enabled('move_and_grab')  # the GUI is not blocked, the action is disabled
    qtbot.waitUntil(lambda: not ext._busy, timeout=15000)

    assert ext.settings['status'] == 'Done'
    position = ext._positions.get_data_from_name('Move')
    assert position.units == actuator.units  # the target and the positions have the units of the actuator
    assert float(position.data[0][0]) == pytest.approx(5., abs=actuator.epsilon)  # reached within the precision
    assert len(ext.viewer.viewers) == 1  # the data of the detector is displayed


def test_cannot_quit_while_busy(extension, qtbot):
    ext, _ = extension
    ext.move_and_grab()
    assert ext._quit_fun() is False
    qtbot.waitUntil(lambda: not ext._busy, timeout=15000)
    assert ext._quit_fun() is True
    ext.modules_manager.timeout_signal.connect(ext._on_timeout)  # reconnected for the quit of the fixture


def test_save(extension, qtbot, tmp_path):
    ext, _ = extension
    ext.h5_manager.get_h5saver().settings['base_path'] = str(tmp_path)  # not in the user's data folder
    ext.settings['save'] = True
    ext.move_and_grab()
    qtbot.waitUntil(lambda: not ext._busy, timeout=15000)

    h5saver = ext.h5_manager.h5saver
    group = h5saver.get_node('/RawData/MoveAndGrab')
    assert len(h5saver.get_children(group)) > 0  # the position and the data have been saved
