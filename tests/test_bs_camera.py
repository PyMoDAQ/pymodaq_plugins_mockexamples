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
