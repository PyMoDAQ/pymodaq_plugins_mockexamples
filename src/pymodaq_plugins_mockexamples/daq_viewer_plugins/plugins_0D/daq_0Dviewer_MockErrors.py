from pymodaq_plugins_mock.daq_viewer_plugins.plugins_0D.daq_0Dviewer_Mock import DAQ_0DViewer_Mock
from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters

from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_mockexamples.hardware.random_wrapper import RandomWrapper


class DAQ_0DViewer_MockErrors(DAQ_0DViewer_Mock):

    hardware_averaging = True


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
        data_tot = []
        errors_tot = []
        labels = []

        for mock_param, data in zip(self.settings.child('mocks').children(), self.data_mock):
            if mock_param.value():
                data = np.roll(data, self.ind_data)
                if Naverage > 1:
                    data_tot.append(np.atleast_1d(np.mean(data[0:Naverage - 1])))
                    errors_tot.append(np.atleast_1d(np.std(data[0:Naverage - 1])))
                else:
                    data_tot.append(np.array([data[0]]))
                    errors_tot.append(None)

                labels.append(mock_param.name())

        if not data_tot:
            return

        if self.settings['sep_viewers']:
            self.dte_signal.emit(DataToExport('Mock0D',
                                              data=[DataFromPlugins(name=label,
                                                                    data=[data],
                                                                    dim='Data0D',
                                                                    labels=[label],
                                                                    errors=[errors] if errors is not None else None)
                                                    for label, data, errors in zip(labels, data_tot, errors_tot)]))
        else:
            self.dte_signal.emit(DataToExport('Mock0D',
                                              data=[DataFromPlugins(name='Mock0D',
                                                                    data=data_tot,
                                                                    dim='Data0D',
                                                                    labels=labels,
                                                                    errors=errors_tot if errors_tot[0] is not None else None)]))
        self.ind_data += 1

if __name__ == '__main__':
    main(__file__)
