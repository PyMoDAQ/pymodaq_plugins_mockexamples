"""Cookbook recipe 3b: 2D detector for a camera, on the camera base class of ``pymodaq_plugins_utils``.

COPY this file for a camera. It is short because ``CameraBase`` does the work: acquisition in a thread of its own that
waits for the frames of the camera, snap and live modes, averaging, the ROI drawn in the viewer applied by the camera
("Update ROI from Viewer", "Apply ROI", "Clear ROI+Bin"), the binning, the exposure time, the FPS, the colour conversion
and the axes of the viewer (in um if the driver knows the pixel size, else in pixels).
ADAPT: ``ini_detector_custom``, which creates the camera driver. The driver follows ``CameraDriverBase``
(``pymodaq_plugins_utils.hardware.camera_driver``), whose methods are those of the pylablib cameras: use one of them
as it is (see ``CameraBasePyLabLib`` for those) or write yours, as ``hardware/mock_camera.py`` does for a simulated one.
Add the settings of your camera to ``params`` and handle them in ``commit_settings`` after calling the one of the base.
KEEP:
- the master/slave handling in ``ini_detector_custom``: alone the plugin owns the camera, with the same controller ID
  as another module it uses the camera of the master;
- ``params = comon_parameters + cam_params``: the settings ``CameraBase`` reads (exposure, ROI, binning, buffer...).

``BSCamera`` is the other camera of the package: there the plugin itself does the readout of a simulated sensor, which
shows the ROI, the binning and the calibrated axes without a base class.

Who runs where (GUI thread, plugin thread, driver thread): see the diagrams of "How an instrument plugin works with the
Dashboard" (``plugin_workflow``) in the developer guide of PyMoDAQ.
"""
from pymodaq.control_modules.viewer_utility_classes import comon_parameters, main

from pymodaq_plugins_utils.hardware.camera_base import CameraBase, cam_params

from pymodaq_plugins_mockexamples.hardware.mock_camera import MockCamera


class DAQ_2DViewer_CookbookCamera(CameraBase):
    """A simulated 256 x 256 camera with 5.5 um pixels, looking at a Gaussian spot

    The exposure time sets the frame rate (at least 10 ms) and the signal. Draw a ROI in the viewer, click "Update ROI
    from Viewer" then "Apply ROI" to read only that part of the sensor; change the binning to sum pixels.
    """
    params = comon_parameters + cam_params

    def ini_detector_custom(self, controller=None):
        """Create the camera (master) or take the one of the master (slave)"""
        if self.is_master:
            self.controller = MockCamera()
        else:
            self.controller = controller


if __name__ == '__main__':
    main(__file__)
