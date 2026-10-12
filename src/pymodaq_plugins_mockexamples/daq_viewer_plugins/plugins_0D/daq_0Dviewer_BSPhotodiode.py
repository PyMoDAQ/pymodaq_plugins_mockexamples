from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters

from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport


from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_2D.daq_2Dviewer_BSCamera import (
    DAQ_2DViewer_BSCamera)


class DAQ_0DViewer_BSPhotodiode(DAQ_2DViewer_BSCamera):
    """ Simulate the overall power send on to the Camera"""

    def average_data(self, Naverage, init=False):
        data_tmp = np.zeros_like(self.controller.get_photodiode_data())
        for ind in range(Naverage):
            data_tmp += self.controller.get_photodiode_data()
        data_tmp = data_tmp / Naverage

        dwa = DataFromPlugins(name='BSCamera', data=[np.array([float(data_tmp)])],
                              )

        return DataToExport('BSCamera', data=[dwa])


if __name__ == '__main__':
    main(__file__)
