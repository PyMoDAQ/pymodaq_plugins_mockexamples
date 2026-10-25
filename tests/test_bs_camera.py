"""The beam steering camera: several images, fringes and drift on top of the spot moved by the piezo mirror"""
import numpy as np
import pytest

from pymodaq.utils.plugin_testing import make_detector, grab_and_wait

from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_2D.daq_2Dviewer_BSCamera import DAQ_2DViewer_BSCamera
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_2D.daq_2Dviewer_RoiStuff import DAQ_2DViewer_RoiStuff


@pytest.fixture
def camera(qapp):
    plugin = make_detector(DAQ_2DViewer_BSCamera)
    yield plugin
    plugin.close()


def test_one_image_by_default(camera):
    dte = grab_and_wait(camera)
    assert len(dte) == 1
    assert dte[0].shape == (256, 256)


def test_several_panels_and_colors(camera):
    camera.settings.child('Nimagespannel').setValue(2)
    camera.settings.child('Nimagescolor').setValue(3)
    dte = grab_and_wait(camera)
    assert len(dte) == 2
    assert len(dte[0]) == 3
    assert np.allclose(dte[0][2], 3 * dte[0][0])


def test_fringes_modulate_the_spot(camera):
    plain = grab_and_wait(camera)[0][0]
    camera.settings.child('fringes').setValue(True)
    camera.commit_settings(camera.settings.child('fringes'))
    fringes = grab_and_wait(camera)[0][0]
    assert fringes.max() < plain.max() * 1.5  # power noise differs between grabs
    assert not np.allclose(fringes / fringes.max(), plain / plain.max())


def test_drift_moves_the_spot(camera):
    camera.settings.child('is_drifting').setValue(True)
    camera.commit_settings(camera.settings.child('is_drifting'))
    camera.settings.child('is_drifting', 'drift_x').setValue(10.)
    camera.commit_settings(camera.settings.child('is_drifting', 'drift_x'))
    first = grab_and_wait(camera)[0][0]
    for _ in range(3):
        last = grab_and_wait(camera)[0][0]
    assert np.argmax(last.sum(axis=0)) < np.argmax(first.sum(axis=0))  # the spot moves toward lower x


def test_roi_stuff_is_a_beam_steering_camera(qapp):
    plugin = make_detector(DAQ_2DViewer_RoiStuff)
    try:
        assert isinstance(plugin, DAQ_2DViewer_BSCamera)
        assert grab_and_wait(plugin)[0].shape == (256, 256)
    finally:
        plugin.close()


def _axis(dwa, label):
    return next(axis for axis in dwa.axes if axis.label == label)


def _set(camera, name, value, *path):
    param = camera.settings.child('sensor', *path, name)
    param.setValue(value)
    camera.commit_settings(param)


def test_axes_are_calibrated_in_um(camera):
    axis = _axis(grab_and_wait(camera)[0], 'x')
    assert axis.units == 'um'
    assert axis.size == 256
    assert axis.scaling == pytest.approx(5.5)
    assert axis.offset == pytest.approx(0.)


def test_roi_crops_the_image_and_moves_the_axes(camera):
    for name, value in (('roi_x', 100), ('roi_y', 50), ('roi_width', 64), ('roi_height', 32)):
        _set(camera, name, value, 'roi')
    dwa = grab_and_wait(camera)[0]
    assert dwa.shape == (32, 64)
    x_axis, y_axis = _axis(dwa, 'x'), _axis(dwa, 'y')
    assert x_axis.offset == pytest.approx(100 * 5.5)
    assert y_axis.offset == pytest.approx(50 * 5.5)
    assert x_axis.units == y_axis.units == 'um'


def test_roi_stays_on_the_beam_position(camera):
    """The beam sits at pixel 128: it is at the same place in um with or without the ROI"""
    _set(camera, 'roi_x', 64, 'roi')
    _set(camera, 'roi_width', 128, 'roi')
    dwa = grab_and_wait(camera)[0][0]
    x_axis = camera.x_axis.get_data()
    assert x_axis[np.argmax(dwa.sum(axis=0))] == pytest.approx(128 * 5.5, abs=2 * 5.5)


def test_binning_sums_pixels_and_scales_the_axes(camera):
    plain = grab_and_wait(camera)[0]
    _set(camera, 'binning', 4)
    binned = grab_and_wait(camera)[0]
    assert binned.shape == (64, 64)
    assert _axis(binned, 'x').scaling == pytest.approx(4 * 5.5)
    assert _axis(binned, 'x').offset == pytest.approx(1.5 * 5.5)  # centre of the first 4 pixels
    # the signal is summed: same total as without binning, up to the power noise of the beam
    assert binned[0].sum() == pytest.approx(plain[0].sum(), rel=0.3)


def test_binning_drops_incomplete_pixels(camera):
    _set(camera, 'roi_width', 10, 'roi')
    _set(camera, 'binning', 4)
    assert grab_and_wait(camera)[0].shape == (64, 2)


def test_exposure_scales_the_signal(camera):
    camera.settings.child('power_noise').setValue(1e6)  # no noise on the beam power
    camera.commit_settings(camera.settings.child('power_noise'))
    ref = grab_and_wait(camera)[0][0].max()
    _set(camera, 'exposure_ms', 50.)
    assert grab_and_wait(camera)[0][0].max() == pytest.approx(ref / 2, rel=0.1)


def test_roi_stuff_follows_the_hardware_roi(qapp):
    plugin = make_detector(DAQ_2DViewer_RoiStuff)
    try:
        param = plugin.settings.child('sensor', 'roi', 'roi_width')
        param.setValue(100)
        plugin.commit_settings(param)
        dwa = grab_and_wait(plugin)[0]
        assert dwa.shape == (256, 100)
        assert _axis(dwa, 'scaled X').size == 100
    finally:
        plugin.close()
