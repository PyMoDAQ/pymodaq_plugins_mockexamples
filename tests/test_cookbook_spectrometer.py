"""The spectrometer recipe: the simulated instrument, the 1D detector (calibrated axis) and the actuator of the grating

To test your own plugins copy the last part and replace the plugin classes.
"""
import time

import numpy as np
import pytest

from pymodaq.utils.plugin_testing import make_actuator, make_detector, move_abs_and_wait, move_home_and_wait, \
    grab_and_wait

from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_CookbookSpectrometer import \
    DAQ_Move_CookbookSpectrometer
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_1D.daq_1Dviewer_CookbookSpectrometer import \
    DAQ_1DViewer_CookbookSpectrometer
from pymodaq_plugins_mockexamples.hardware.spectrometer import Spectrometer


@pytest.fixture
def spectrometer():
    spectro = Spectrometer()
    spectro.tau = 0.05
    return spectro


class TestInstrument:
    def test_axis_is_centred_and_follows_the_grating(self, spectrometer):
        spectrometer.set_wavelength(600.)
        while spectrometer.moving:
            time.sleep(0.01)
        axis = spectrometer.get_wavelength_axis()
        assert len(axis) == Spectrometer.Nx
        assert axis[Spectrometer.Nx // 2] == pytest.approx(600.)
        assert np.diff(axis) == pytest.approx(spectrometer.dispersion)

    def test_dispersion_depends_on_the_grating(self, spectrometer):
        wide = np.ptp(spectrometer.get_wavelength_axis())
        spectrometer.grating = 'G1200'
        assert np.ptp(spectrometer.get_wavelength_axis()) < wide

    def test_unknown_grating(self, spectrometer):
        with pytest.raises(ValueError):
            spectrometer.grating = 'G1'

    def test_negative_wavelength(self, spectrometer):
        with pytest.raises(ValueError):
            spectrometer.set_wavelength(-1.)

    def test_the_grating_takes_time(self, spectrometer):
        spectrometer.tau = 10
        spectrometer.set_wavelength(600.)
        assert spectrometer.moving
        assert 532 <= spectrometer.get_wavelength() < 600

    def test_peak_is_at_the_right_wavelength(self, spectrometer):
        spectrometer.peak_wavelength = 540.
        axis = spectrometer.get_wavelength_axis()
        spectrum = spectrometer.grab_spectrum()
        assert axis[np.argmax(spectrum)] == pytest.approx(540., abs=spectrometer.dispersion)


@pytest.fixture
def detector(qapp):
    plugin = make_detector(DAQ_1DViewer_CookbookSpectrometer)
    plugin.controller.tau = 0.05
    yield plugin
    plugin.close()


def _wait_for_the_grating(spectrometer):
    while spectrometer.moving:
        time.sleep(0.01)


class TestDetector:
    def test_grab_has_a_wavelength_axis_in_nm(self, detector):
        dwa = grab_and_wait(detector)[0]
        assert dwa.shape == (Spectrometer.Nx,)
        assert dwa.axes[0].units == 'nm'
        assert dwa.axes[0].label == 'wavelength'

    def test_axis_follows_the_central_wavelength(self, detector):
        param = detector.settings.child('central_wavelength')
        param.setValue(600.)
        detector.commit_settings(param)
        _wait_for_the_grating(detector.controller)
        axis = grab_and_wait(detector)[0].axes[0].get_data()
        assert axis[len(axis) // 2] == pytest.approx(600.)

    def test_line_is_in_the_right_place(self, detector):
        detector.controller.peak_wavelength = 535.
        dwa = grab_and_wait(detector)[0]
        axis = dwa.axes[0].get_data()
        assert axis[np.argmax(dwa[0])] == pytest.approx(535., abs=1.)

    def test_grating_changes_the_range(self, detector):
        wide = np.ptp(grab_and_wait(detector)[0].axes[0].get_data())
        param = detector.settings.child('grating')
        param.setValue('G1200')
        detector.commit_settings(param)
        assert np.ptp(grab_and_wait(detector)[0].axes[0].get_data()) < wide


class TestMasterSlave:
    def test_actuator_turns_the_grating_of_the_detector(self, detector):
        actuator = make_actuator(DAQ_Move_CookbookSpectrometer, controller=detector.controller)
        try:
            assert actuator.controller is detector.controller
            position = move_abs_and_wait(actuator, 580.)
            assert position.value('nm') == pytest.approx(580., abs=0.1)
            axis = grab_and_wait(detector)[0].axes[0].get_data()
            assert axis[len(axis) // 2] == pytest.approx(580., abs=0.2)
        finally:
            actuator.close()  # a slave never closes the shared instrument
        assert grab_and_wait(detector)[0].shape == (Spectrometer.Nx,)

    def test_slave_detector_does_not_move_the_grating(self, qapp):
        actuator = make_actuator(DAQ_Move_CookbookSpectrometer)
        try:
            actuator.controller.tau = 0.05
            move_abs_and_wait(actuator, 560.)
            detector = make_detector(DAQ_1DViewer_CookbookSpectrometer, controller=actuator.controller)
            try:
                assert actuator.get_actuator_value().value('nm') == pytest.approx(560., abs=0.1)
                assert detector.settings['central_wavelength'] == pytest.approx(560., abs=0.1)
            finally:
                detector.close()
        finally:
            actuator.close()


class TestActuator:
    def test_move_home(self, qapp):
        actuator = make_actuator(DAQ_Move_CookbookSpectrometer)
        try:
            actuator.controller.tau = 0.05
            assert actuator.get_actuator_value().units == 'nm'
            assert move_home_and_wait(actuator).value('nm') == pytest.approx(600., abs=0.1)
        finally:
            actuator.close()
