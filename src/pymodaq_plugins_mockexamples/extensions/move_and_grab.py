"""Reference Dashboard extension: move an actuator, grab a detector, show the data and save them.

It is the smallest useful ``CustomExt`` and shows what an extension driving instruments has to get right:

* it uses the actuators and detectors of the Dashboard through ``self.modules_manager`` and never creates control
  modules, nor its own experiment or state managers
* it never blocks the GUI thread: the move and the grab are started with a callback, the next step is done in the callback
  when the control module signals that it is finished (no polling, no sleep)
* the position is a ``DataActuator`` with units (the ones of the actuator), the data come back as a ``DataToExport``
* the extension can be closed cleanly: callbacks are forgotten, the file is closed, and quitting is refused while busy

Read the page "How a Dashboard extension works" of the PyMoDAQ documentation for the structure.
"""
from qtpy import QtWidgets

from pymodaq_utils.logger import set_logger, get_module_name

from pymodaq_data import DataToExport
from pymodaq_data.h5modules.data_saving import DataToExportSaver

from pymodaq_gui import utils as gutils
from pymodaq_gui.plotting.data_viewers import ViewerDispatcher

from pymodaq.control_modules.enums import MoveType
from pymodaq.utils.custom_ext import CustomExt
from pymodaq.utils.data import DataActuator
from pymodaq.utils.managers.modules import ModuleType

logger = set_logger(get_module_name(__file__))

EXTENSION_NAME = 'Move and Grab'  # displayed in the Extensions menu of the Dashboard
CLASS_NAME = 'MoveAndGrab'  # the name of the class below


class MoveAndGrab(CustomExt):

    params = [
        {'title': 'Actuator:', 'name': 'actuator', 'type': 'list', 'limits': []},
        {'title': 'Target:', 'name': 'target', 'type': 'float', 'value': 1.},  # in the units of the actuator
        {'title': 'Detector:', 'name': 'detector', 'type': 'list', 'limits': []},
        {'title': 'Save the data:', 'name': 'save', 'type': 'bool', 'value': False},
        {'title': 'Status:', 'name': 'status', 'type': 'str', 'value': 'Idle', 'readonly': True},
    ]

    def __init__(self, parent: gutils.DockArea, dashboard):
        super().__init__(parent, dashboard)  # also creates self.modules_manager for this extension
        self._busy = False
        self._positions: DataToExport = None
        self.setup_ui()

    def setup_docks_and_widgets(self):
        self.docks['settings'] = gutils.Dock('Settings')
        self.dockarea.addDock(self.docks['settings'])
        self.docks['settings'].addWidget(self.settings_tree)

        self.viewer = ViewerDispatcher(self.dockarea, title='Data')  # shows each data of a DataToExport, in docks

    def setup_menus_and_toolbars(self, menubar: QtWidgets.QMenuBar = None):
        self.create_dashboard_toolbar(add_break=False)  # show/hide the Dashboard, experiment and state

    def setup_actions(self):
        self.add_action('move_and_grab', 'Move and grab', 'camera',
                        tip='Move the selected actuator to the target, then grab the selected detector')

    def connect_things(self):
        self.connect_action('move_and_grab', self.move_and_grab)
        self.modules_manager.timeout_signal.connect(self._on_timeout)

    def do_things_after_experiment_set(self, experiment_name: str, show_dashboard: bool = None):
        """The instruments just changed: refresh what depends on them (the base class updates the modules_manager)"""
        super().do_things_after_experiment_set(experiment_name, show_dashboard)
        self.settings.child('actuator').setLimits(self.modules_manager.actuators_name)
        self.settings.child('detector').setLimits(self.modules_manager.detectors_name)

    def move_and_grab(self):
        if self._busy:
            return
        actuator = self.modules_manager.get_mod_from_name(self.settings['actuator'], ModuleType.Actuator)
        detector = self.modules_manager.get_mod_from_name(self.settings['detector'], ModuleType.Detector)
        if actuator is None or detector is None:
            self.update_status('Select an actuator and a detector (set an experiment in the Dashboard first)')
            return
        self._set_busy(True, f'Moving {actuator.title}')
        self.modules_manager.selected_actuators_name = [actuator.title]
        self.modules_manager.selected_detectors_name = [detector.title]
        # the target has units: those of the actuator, so that no conversion is needed
        target = DataToExport('target', data=[DataActuator(actuator.title, data=self.settings['target'],
                                                           units=actuator.units)])
        self.modules_manager.move_actuators_with_callback(target, mode=MoveType.ABS, callback=self._on_move_done)

    def _on_move_done(self, positions: DataToExport):
        """Slot called, in the GUI thread, once the actuator reached its target"""
        self.modules_manager.forget_callback(self._on_move_done, ModuleType.Actuator)
        self._positions = positions
        self.set_status('Grabbing')
        self.modules_manager.grab_data_with_callback(callback=self._on_data)

    def _on_data(self, data: DataToExport):
        """Slot called, in the GUI thread, once the detector sent its data"""
        self.modules_manager.forget_callback(self._on_data, ModuleType.Detector)
        self.viewer.show_data(data)
        if self.settings['save']:
            self._save(data)
        self._set_busy(False, 'Done')

    def _save(self, data: DataToExport):
        h5saver = self.h5_manager.h5saver  # opens the file, or creates a new one, if needed
        node = h5saver.get_set_group('/RawData', 'MoveAndGrab')
        DataToExportSaver(h5saver).add_data(node, DataToExport('moveandgrab', data=[*self._positions, *data]))
        h5saver.flush()

    def _on_timeout(self, missing_modules: list):
        """A module did not answer: do not stay blocked"""
        self.modules_manager.forget_callback(self._on_move_done, ModuleType.Control)
        self.modules_manager.forget_callback(self._on_data, ModuleType.Control)
        self._set_busy(False, f'Timeout: {", ".join(missing_modules)}')

    def _set_busy(self, busy: bool, status: str):
        self._busy = busy
        self.set_action_enabled('move_and_grab', not busy)
        self.set_status(status)

    def set_status(self, status: str):
        self.settings.child('status').setValue(status)

    def _quit_fun(self) -> bool:
        """Return True to let the extension quit; False to refuse, here while a move or a grab is going on"""
        if self._busy:
            self.update_status('Wait for the end of the move and grab before quitting')
            return False
        self.modules_manager.timeout_signal.disconnect(self._on_timeout)
        self.h5_manager.close_file()
        return True


def main():
    """Run the extension on its own (the Dashboard stays hidden), see ``-x EXPERIMENT_NAME -s STATE_NAME``"""
    import sys
    from pymodaq_gui.qt_utils import mkQApp
    from pymodaq.dashboard import load_dashboard_with_arguments
    from pymodaq.utils.gui_utils.loader_utils import create_extension

    app = mkQApp('Move and Grab')
    win, dashboard, _ = load_dashboard_with_arguments(show_dashboard=False, load_extension=False)
    win.mainwindow.setVisible(False)
    win_ext, ext = create_extension(dashboard, MoveAndGrab, show_extension=True)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
