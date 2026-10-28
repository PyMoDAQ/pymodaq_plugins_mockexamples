from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters

from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_mockexamples.hardware.beam_steering import BeamSteering


class DAQ_2DViewer_BSCamera(DAQ_Viewer_base):
    """ Generate a 2D image with a spot on it whose position can be set
    using DAQ_Move_BSPiezoMirror

    It is a plain ``DAQ_Viewer_base`` plugin on purpose, it does not follow the shared pattern of
    ``pymodaq_plugins_utils`` (``CameraBase``, settings ``comon_parameters + cam_params``). It is the camera of the
    beam steering demonstrations: its settings (beam, drift, sensor, ROI, binning, exposure) are those the demo
    experiments (``beam_steering.xml``) use, and it must stay short and self-contained to demonstrate the features
    of PyMoDAQ rather than a camera driver. The ROI, the binning and the exposure time are settings of its own,
    applied by its simulated camera. The camera recipe of the cookbook, to copy for a real camera, is
    ``DAQ_2DViewer_CookbookCamera``. Compare also with ``DAQ_2DViewer_RoiStuff``, where the ROI is drawn in the
    viewer and applied by the plugin after the grab.
    """
    live_mode_available = True
    hardware_averaging = True

    params = comon_parameters + [
        {'title': 'Wait time (ms)', 'name': 'wait_time', 'type': 'int', 'value': 100, 'min': 0},
        {'title': 'Beam Size X', 'name': 'size_x', 'type': 'float', 'value': 40, 'min': 10},
        {'title': 'Beam Size Y', 'name': 'size_y', 'type': 'float', 'value': 20, 'min': 10},
        {'title': 'Beam Angle (deg)', 'name': 'angle', 'type': 'float', 'value': 0,},
        {'title': 'Gaussian-ness', 'name': 'index_n', 'type': 'int', 'value': 1, },
        {'title': 'Power noise', 'name': 'power_noise', 'type': 'float', 'value': 10.,
         'tip': 'The lower the value, the higher the noise'},
        {'title': 'Fringes?', 'name': 'fringes', 'type': 'bool', 'value': False},
        {'title': 'Drift', 'name': 'is_drifting', 'type': 'bool', 'value': False, 'children': [
            {'title': 'drift_x', 'name': 'drift_x', 'type': 'float', 'value': 0.,
             'tip': 'Pixels added to the beam position at each grab'},
            {'title': 'drift_y', 'name': 'drift_y', 'type': 'float', 'value': 0.},
            {'title': 'std_x', 'name': 'std_x', 'type': 'float', 'value': 0.,
             'tip': 'Standard deviation of the random walk of the beam position'},
            {'title': 'std_y', 'name': 'std_y', 'type': 'float', 'value': 0.},
        ]},
        {'title': 'Sensor', 'name': 'sensor', 'type': 'group', 'children': [
            {'title': 'Pixel size (um)', 'name': 'pixel_size', 'type': 'float', 'value': 5.5, 'min': 0.1,
             'tip': 'Size of a pixel of the sensor: sets the calibration of the axes'},
            {'title': 'Exposure (ms)', 'name': 'exposure_ms', 'type': 'float', 'value': 100., 'min': 0.1,
             'tip': 'The signal is proportional to the exposure time (100 ms gives the reference signal)'},
            {'title': 'Binning', 'name': 'binning', 'type': 'list', 'value': 1, 'limits': [1, 2, 4, 8],
             'tip': 'Sensor pixels summed along each direction. Pixels that do not fill a bin are dropped'},
            {'title': 'ROI', 'name': 'roi', 'type': 'group', 'children': [
                {'title': 'X (pixel)', 'name': 'roi_x', 'type': 'int', 'value': 0, 'min': 0, 'max': 255},
                {'title': 'Y (pixel)', 'name': 'roi_y', 'type': 'int', 'value': 0, 'min': 0, 'max': 255},
                {'title': 'Width (pixel)', 'name': 'roi_width', 'type': 'int', 'value': 256, 'min': 1, 'max': 256},
                {'title': 'Height (pixel)', 'name': 'roi_height', 'type': 'int', 'value': 256, 'min': 1,
                 'max': 256},
            ]},
        ]},
        {'title': 'Nimages colors:', 'name': 'Nimagescolor', 'type': 'int', 'value': 1, 'min': 1, 'max': 3},
        {'title': 'Nimages pannels:', 'name': 'Nimagespannel', 'type': 'int', 'value': 1, 'min': 1},
        {'title': 'Threshold', 'name': 'threshold', 'type': 'float', 'value': 0., 'min': 0},
    ]

    def ini_attributes(self):
        self.controller: BeamSteering = None
        self.live = False

    def commit_settings(self, param: Parameter):
        """
        """
        if param.name() == 'size_x':
            self.controller.camera.dx = param.value()
        elif param.name() == 'size_y':
            self.controller.camera.dy = param.value()
        elif param.name() == 'angle':
            self.controller.camera.angle = param.value()
        elif param.name() == 'index_n':
            self.controller.camera.n = param.value()
        elif param.name() == 'power_noise':
            self.controller.power_noise_fraction = param.value()
        elif param.name() in ('fringes', 'is_drifting', 'drift_x', 'drift_y', 'std_x', 'std_y'):
            setattr(self.controller.camera, param.name(), param.value())
            if param.name() == 'is_drifting':
                self.controller.camera.refresh_drift()
        elif param.name() in ('pixel_size', 'exposure_ms', 'binning'):
            setattr(self.controller.camera, param.name(), param.value())
            self.update_axes()
        elif param.name().startswith('roi_'):
            self.controller.camera.set_roi(*(self.settings['sensor', 'roi', name] for name in
                                             ('roi_x', 'roi_y', 'roi_width', 'roi_height')))
            self.update_axes()

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = BeamSteering()
        else:
            self.controller = controller
        for name in ('size_x', 'size_y', 'angle', 'index_n', 'power_noise', 'fringes', 'is_drifting', 'drift_x',
                     'drift_y', 'std_x', 'std_y', 'pixel_size', 'exposure_ms', 'binning',
                     'roi_x'):  # apply the settings loaded from a preset (the four ROI values at once)
            self.commit_settings(self.settings.child(*self._path(name)))
        self.emit_status(ThreadCommand('update_main_settings',
                                       [['wait_time'], self.settings['wait_time'], 'value']))

        self.update_axes()

        initialized = True
        info = 'Controller ok'
        return info, initialized

    @staticmethod
    def _path(name: str):
        if name.startswith(('drift', 'std')) and name.endswith(('_x', '_y')):
            return 'is_drifting', name
        if name.startswith('roi_'):
            return 'sensor', 'roi', name
        if name in ('pixel_size', 'exposure_ms', 'binning'):
            return 'sensor', name
        return (name,)

    def _build_axes(self):
        """The axes (x, y) of the images, in um: they follow the ROI and the binning of the camera"""
        camera = self.controller.camera
        x, y = camera.get_axes()
        return (Axis(data=x, label='x', units='um', index=1),
                Axis(data=y, label='y', units='um', index=0))

    def update_axes(self):
        """Axes are sent with the data, so changing them here is enough"""
        self.x_axis, self.y_axis = self._build_axes()

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
        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                # self.live = False  # don't want to use that for the moment

        if self.live:
            while self.live:
                data = self.average_data(Naverage)  # hardware averaging
                QThread.msleep(kwargs.get('wait_time', 100))
                self.dte_signal.emit(data)
                QtWidgets.QApplication.processEvents()
        else:
            data = self.average_data(Naverage)  # hardware averaging
            QThread.msleep(000)
            self.dte_signal.emit(data)

    def average_data(self, Naverage, init=False):
        data_tmp = np.zeros_like(self.controller.get_camera_data())
        for ind in range(Naverage):
            data_tmp += self.controller.get_camera_data()
        data_tmp = data_tmp / Naverage

        data_tmp = data_tmp * (data_tmp >= self.settings['threshold'])
        data = []
        for ind in range(self.settings['Nimagespannel']):
            data.append(DataFromPlugins(
                name=f'BSCamera_{ind:d}',
                data=[(indcolor + 1) * data_tmp for indcolor in range(self.settings['Nimagescolor'])],
                dim='Data2D', axes=[self.x_axis, self.y_axis]))

        return DataToExport('BSCamera', data=data)

    def stop(self):
        """
            not implemented.
        """
        self.live = False
        return ""


if __name__ == '__main__':
    main(__file__)
