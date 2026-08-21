from qtpy.QtCore import QThread

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main
import numpy as np

from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_1D.daq_1Dviewer_Mock_spectro import DAQ_1DViewer_Mock_spectro


class DAQ_1DViewer_MockSpectroErrors(DAQ_1DViewer_Mock_spectro):
    """
        Same as Mock Spectro but each data is the average and std of 10 acquisition -
        testing errors saving/loading purpose
    """


    def grab_data(self, Naverage=1, **kwargs):
        """

        """
        Naverage = 10
        data_tot = [np.zeros(list(dat.shape)+[Naverage]) for dat in self.set_Mock_data()]

        for ind in range(Naverage):
            for ind_list, data_array in enumerate(self.set_Mock_data()):
                data_tot[ind_list][..., ind] = data_array
                QThread.msleep(self.settings.child('exposure_ms').value())

        average = [np.average(data_array, 1) for data_array in data_tot]
        std = [np.std(data_array, 1) for data_array in data_tot]

        self.dte_signal.emit(
            DataToExport(
                'Mock1D',
                data=[
                    DataFromPlugins(name='Mock1D',
                                    data=average,
                                    errors= std,
                                    dim='Data1D',
                                    axes=[self.x_axis])]))


if __name__ == '__main__':
    main(__file__)
