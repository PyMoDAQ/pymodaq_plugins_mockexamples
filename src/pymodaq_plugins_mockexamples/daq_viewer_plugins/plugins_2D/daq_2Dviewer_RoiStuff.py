from typing import Iterable

from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
from pymodaq.control_modules.viewer_utility_classes import main

from pymodaq_gui.plotting.items.roi import RoiInfo
from pymodaq_data.data import DataToExport, DataWithAxes, Axis
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_2D.daq_2Dviewer_MockCamera import DAQ_2DViewer_MockCamera


class DAQ_2DViewer_RoiStuff(DAQ_2DViewer_MockCamera):

    params = DAQ_2DViewer_MockCamera.params + \
             [{'title': 'Use Roi:', 'name': 'use_roi', 'type': 'bool'}]

    def ini_attributes(self):
        super().ini_attributes()
        self.roi_select_info: RoiInfo = None
        self.roi_select_viewer_index: int = None

    def ini_detector(self, controller=None):
        info, initialized = super().ini_detector(controller)



        self.x_axis = Axis(size=self.controller.Nx, offset=23,
                           scaling=0.5, label='scaled X', index=1)
        self.y_axis = Axis(size=self.controller.Ny,
                           offset=-16,
                           scaling=2., label='scaled Y', index=0)

        return info, initialized

    def ROISelect(self, info: QRectF):
        raise DeprecationWarning('Do not use it anymore, use the roi_select method')

    def roi_select(self, roi_info: RoiInfo, ind_viewer: int = 0):
        self.roi_select_info = roi_info
        self.roi_select_viewer_index = ind_viewer

    def crosshair(self, crosshair_info: Iterable[float], ind_viewer: int = 0):
        print(crosshair_info)

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

        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                # self.live = False  # don't want to use that for the moment

        if self.live:
            while self.live:
                data: DataToExport = self.average_data(Naverage)  # hardware averaging
                QThread.msleep(kwargs.get('wait_time', 100))
                if self.settings['use_roi']:
                    dte = DataToExport('cropped')
                    for dwa in data.data:
                        dwa_sliced = dwa.vsig[self.roi_select_info.to_slices(False)]
                        dwa.add_extra_attribute(sliced=True)
                        dte.data.append(dwa_sliced)
                self.dte_signal.emit(data)
                QtWidgets.QApplication.processEvents()
        else:
            data = self.average_data(Naverage)  # hardware averaging
            QThread.msleep(000)

        self.live = False  # don't want to use that for the moment

        data: DataToExport = self.average_data(Naverage)  # hardware averaging
        QThread.msleep(kwargs.get('wait_time', 100))
        if self.settings['use_roi']:
            self.roi_select_info.center_origin()
            dte = DataToExport('cropped')
            for dwa in data.data:
                dwa_sliced = dwa.vsig[self.roi_select_info.to_slices(False)]
                dwa.add_extra_attribute(sliced=True)
                dte.data.append(dwa_sliced)
        else:
            dte = data
        self.dte_signal.emit(dte)


if __name__ == '__main__':
    main(__file__)
