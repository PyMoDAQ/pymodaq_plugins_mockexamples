from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters

from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq_gui.parameter import Parameter


from pymodaq_plugins_mockexamples.hardware.complex_signal import DataSignal


class DAQ_0DViewer_MockComplexSignal(DAQ_Viewer_base):
    """ To be used to probe Complex data signal generated using Gaussians, Loretzian or other complex data
    Can span 1D (Lorentzian) or 2D space (all types). Should be coupled with the MockComplexSignal actuators
    within a preset"""

    live_mode_available = False
    hardware_averaging = False

    params = comon_parameters + [
        {'title': 'Signal type', 'name': 'signal_type', 'type': 'list', 'limits': DataSignal.signal_types},
        {'title': 'refresh structures', 'name': 'refresh', 'type': 'bool_push', 'label': 'Refresh'},
        {'title': 'Nstruct', 'name': 'n_struct', 'type': 'int', 'value': 5, 'min': 1},
        {'title': 'Wait time (ms)', 'name': 'wait_time', 'type': 'int', 'value': 100, 'default': 100, 'min': 0},
    ]

    def ini_attributes(self):
        self.controller: DataSignal = None

    def commit_settings(self, param: Parameter):
        """
        """
        if param.name() == 'signal_type':
            self.controller.signal_type = param.value()
        elif param.name() == 'refresh':
            self.controller.ini_random_structures()
        elif param.name() == 'n_struct':
            self.controller.Nstruct = param.value()
            self.controller.ini_random_structures()

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = DataSignal()
            self.controller.ini_random_structures()
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
        data = DataFromPlugins(name='ComplexSignal', data=[np.array([self.controller.get_data_0D()])])
        self.dte_signal.emit(DataToExport('Data', data=[data]))

    def stop(self):
        """

        """
        return ""


if __name__ == '__main__':
    main(__file__)
