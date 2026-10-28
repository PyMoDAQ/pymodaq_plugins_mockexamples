"""The camera recipe: a camera driver with its own thread behind the camera base class of pymodaq_plugins_utils"""
import time

import numpy as np
import pytest

from pymodaq.utils.plugin_testing import make_detector, grab_and_wait, wait_for_signal

from pymodaq_gui.plotting.items.roi import RoiInfo

from pymodaq_plugins_utils.hardware.camera_driver import CameraDriverBase

from pymodaq_plugins_mockexamples.hardware.mock_camera import MockCamera
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_2D.daq_2Dviewer_CookbookCamera import (
    DAQ_2DViewer_CookbookCamera)


@pytest.fixture
def driver():
    camera = MockCamera()
    camera.set_exposure(0.02)
    yield camera
    camera.close()


@pytest.fixture
def camera(qapp):
    plugin = make_detector(DAQ_2DViewer_CookbookCamera)
    plugin.settings.child('timing_opts', 'exposure_time').setValue(20)
    plugin.commit_settings(plugin.settings.child('timing_opts', 'exposure_time'))
    yield plugin
    plugin.close()


def click_led(plugin, name: str):
    """What the user does: press the (checkable) button of the parameter, which the DAQ_Viewer sends to the plugin"""
    param = plugin.settings.child('roi', name)
    param.opts['checked'] = True
    param.activate()


def apply_roi(plugin, rows_um: slice, columns_um: slice):
    plugin.roi_select(RoiInfo.from_slices([rows_um, columns_um]))
    click_led(plugin, 'update_roi')
    click_led(plugin, 'apply_roi')


class TestMockCamera:
    def test_follows_the_driver_contract(self, driver):
        assert isinstance(driver, CameraDriverBase)
        not_implemented = [name for name in dir(CameraDriverBase)
                           if not name.startswith('_') and getattr(MockCamera, name) is getattr(CameraDriverBase, name)
                           and name not in ('get_roi_limits', 'set_frame_format')]
        assert not_implemented == []

    def test_frames_arrive_in_the_buffer_of_its_own_thread(self, driver):
        driver.setup_acquisition()
        driver.start_acquisition()
        assert driver.acquisition_in_progress()
        driver.wait_for_frame(since='start', nframes=3, timeout=2)
        frames, (first, last) = driver.read_multiple_images(return_rng=True)
        assert frames.dtype == np.uint16
        assert frames.shape[1:] == (256, 256)
        assert last - first == len(frames) >= 3
        assert driver.read_multiple_images().shape[0] <= 1  # what was read is not given again

    def test_wait_times_out_when_nothing_is_acquired(self, driver):
        driver.set_exposure(1)
        driver.setup_acquisition()
        driver.start_acquisition()
        with pytest.raises(TimeoutError):
            driver.wait_for_frame(since='now', timeout=0.05)

    def test_stopping_releases_a_waiting_thread(self, driver):
        driver.setup_acquisition()
        driver.start_acquisition()
        driver.clear_acquisition()
        t0 = time.perf_counter()
        driver.wait_for_frame(since='now', timeout=2)  # returns at once, the acquisition is stopped
        assert time.perf_counter() - t0 < 0.5
        assert not driver.acquisition_in_progress()

    def test_roi_and_binning_make_a_smaller_image(self, driver):
        driver.set_roi(hstart=10, hend=110, vstart=20, vend=60, hbin=2, vbin=4)
        assert driver.get_data_dimensions() == (10, 50)
        driver.setup_acquisition()
        driver.start_acquisition()
        driver.wait_for_frame(since='start', timeout=2)
        assert driver.read_newest_image().shape == (10, 50)

    def test_wrong_roi_is_refused(self, driver):
        with pytest.raises(ValueError):
            driver.set_roi(hstart=0, hend=300)
        with pytest.raises(ValueError):
            driver.set_roi(hstart=0, hend=10, hbin=20)

    def test_roi_cannot_change_during_the_acquisition(self, driver):
        driver.setup_acquisition()
        driver.start_acquisition()
        with pytest.raises(RuntimeError):
            driver.set_roi(hstart=10, hend=20, vstart=10, vend=20)

    def test_signal_is_proportional_to_the_exposure(self, driver):
        means = []
        for exposure in (0.02, 0.04):
            driver.clear_acquisition()
            driver.set_exposure(exposure)
            driver.setup_acquisition()
            driver.start_acquisition()
            driver.wait_for_frame(since='start', timeout=2)
            means.append(driver.read_newest_image().astype(float).mean())
        assert means[1] == pytest.approx(2 * means[0], rel=0.1)


class TestPlugin:
    def test_snap(self, camera):
        dte = grab_and_wait(camera)
        assert dte[0].shape == (256, 256)
        assert dte[0][0].max() > 100

    def test_average_is_made_by_the_plugin(self, camera):
        dte = grab_and_wait(camera, naverage=3)
        assert dte[0].shape == (256, 256)

    def test_axes_are_in_um(self, camera):
        dte = grab_and_wait(camera)
        assert camera.x_axis.units == 'µm'
        assert camera.x_axis.scaling == pytest.approx(5.5)
        assert camera.settings['camera_name'] == 'Mock camera (cookbook)'

    def test_live_gives_images_until_stopped(self, camera):
        received = []
        camera.dte_signal.connect(received.append)
        wait_for_signal(camera.dte_signal, lambda: camera.grab_data(1, live=True), timeout_ms=3000)
        wait_for_signal(camera.dte_signal, lambda: None, timeout_ms=3000)
        camera.stop()
        assert len(received) >= 2
        assert not camera.controller.acquisition_in_progress()

    def test_roi_drawn_in_the_viewer_is_applied_by_the_camera(self, camera):
        apply_roi(camera, rows_um=slice(110, 220), columns_um=slice(55, 165))  # um: pixels 20 to 40 and 10 to 30
        assert camera.controller.get_roi() == (10, 30, 20, 40, 1, 1)
        dte = grab_and_wait(camera)
        assert dte[0].shape == (20, 20)
        assert camera.x_axis.offset == pytest.approx(10 * 5.5)

    def test_binning_keeps_the_roi_and_scales_the_axes(self, camera):
        apply_roi(camera, rows_um=slice(110, 220), columns_um=slice(55, 165))
        for name in ('x_binning', 'y_binning'):
            camera.settings.child('roi', name).setValue(2)
            camera.commit_settings(camera.settings.child('roi', name))
        assert camera.controller.get_roi() == (10, 30, 20, 40, 2, 2)
        dte = grab_and_wait(camera)
        assert dte[0].shape == (10, 10)
        assert camera.x_axis.scaling == pytest.approx(11.)

    def test_clear_roi(self, camera):
        apply_roi(camera, rows_um=slice(110, 220), columns_um=slice(55, 165))
        clear = camera.settings.child('roi', 'clear_roi')
        clear.setValue(True)
        camera.commit_settings(clear)
        assert camera.controller.get_roi() == (0, 256, 0, 256, 1, 1)

    def test_close_stops_the_thread_of_the_camera(self, qapp):
        plugin = make_detector(DAQ_2DViewer_CookbookCamera)
        grab_and_wait(plugin)
        controller = plugin.controller
        plugin.close()
        assert not controller.acquisition_in_progress()

    def test_roi_can_change_during_the_live_and_the_plugin_still_closes(self, qapp):
        plugin = make_detector(DAQ_2DViewer_CookbookCamera)
        try:
            plugin.settings.child('timing_opts', 'exposure_time').setValue(20)
            plugin.commit_settings(plugin.settings.child('timing_opts', 'exposure_time'))
            wait_for_signal(plugin.dte_signal, lambda: plugin.grab_data(1, live=True), timeout_ms=3000)
            apply_roi(plugin, rows_um=slice(110, 220), columns_um=slice(55, 165))
            assert plugin.controller.get_roi() == (10, 30, 20, 40, 1, 1)
        finally:
            plugin.close()  # would block if the thread waiting for the frames never ended
