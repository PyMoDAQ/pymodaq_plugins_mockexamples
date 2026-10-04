from typing import Iterable

from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_utils.logger import set_logger, get_module_name

from pymodaq_gui.plotting.items.roi import RoiInfo
from pymodaq_data.data import DataToExport, DataWithAxes, Axis
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_2D.daq_2Dviewer_MockCamera import DAQ_2DViewer_MockCamera

logger = set_logger(get_module_name(__file__))


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
        logger.info(f'Crosshair position in viewer {ind_viewer}: {crosshair_info}')

    def crop(self, data: DataToExport) -> DataToExport:
        """Crop all the data to the ROI select, if 'Use Roi' is checked and a selection has been made

        The RoiInfo is given in the units of the viewer axes (here scaled), so the value-based slicer vsig is used
        """
        if not self.settings['use_roi'] or self.roi_select_info is None:
            return data
        slices = self.roi_select_info.to_slices(False)
        dte = DataToExport('cropped')
        for dwa in data:
            dwa_sliced = dwa.vsig[slices]
            dwa_sliced.add_extra_attribute(sliced=True)
            dte.append(dwa_sliced)
        return dte

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
        if kwargs.get('live', False):
            self.live = True

        if self.live:
            while self.live:
                data = self.average_data(Naverage)  # hardware averaging
                QThread.msleep(kwargs.get('wait_time', 100))
                self.dte_signal.emit(self.crop(data))
                QtWidgets.QApplication.processEvents()
        else:
            data = self.average_data(Naverage)  # hardware averaging
            self.dte_signal.emit(self.crop(data))


if __name__ == '__main__':
    main(__file__)
