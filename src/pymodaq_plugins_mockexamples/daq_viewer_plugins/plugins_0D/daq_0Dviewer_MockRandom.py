from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters

from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_mockexamples.hardware.random_wrapper import RandomWrapper


class DAQ_0DViewer_MockRandom(DAQ_Viewer_base):

    live_mode_available = False
    hardware_averaging = False

    params = comon_parameters + [
        {'title': 'Wait time (ms)', 'name': 'wait_time', 'type': 'int', 'value': 100, 'default': 100, 'min': 0},
    ]

    def ini_attributes(self):
        self.controller: RandomWrapper = None

    def commit_settings(self, param: Parameter):
        """
        """
        pass

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = RandomWrapper()
        else:
            self.controller = controller
        self.emit_status(ThreadCommand('update_main_settings',
                                       [['wait_time'], self.settings['wait_time'], 'value']))

        initialized = True
        info = 'Controller ok'
        return info, initialized

    def close(self):
        pass

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        data = DataFromPlugins(name='RandomData', data=[np.array([self.controller.get_data_0D()])])
        QThread.msleep(10)
        self.dte_signal.emit(DataToExport('Random', data=[data]))

    def stop(self):
        """

        """
        return ""


if __name__ == '__main__':
    main(__file__)
