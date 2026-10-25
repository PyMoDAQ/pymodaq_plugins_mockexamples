"""Behaviour of the cookbook plugins on their simulated device (port ``MOCK``): no hardware, no visible GUI.

The three recipes have the same behaviour, so the same tests apply. To test your own plugin copy this file and
replace the classes of ``RECIPES``.
"""
import time

import pytest

from pymodaq.utils.plugin_testing import (make_actuator, make_detector, move_abs_and_wait, move_rel_and_wait,
                                          move_home_and_wait, grab_and_wait, assert_units)

from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_CookbookSerial import DAQ_Move_CookbookSerial
from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_CookbookVisa import DAQ_Move_CookbookVisa
from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_CookbookPymeasure import DAQ_Move_CookbookPymeasure
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_0D.daq_0Dviewer_CookbookSerial import \
    DAQ_0DViewer_CookbookSerial
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_0D.daq_0Dviewer_CookbookVisa import \
    DAQ_0DViewer_CookbookVisa
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_0D.daq_0Dviewer_CookbookPymeasure import \
    DAQ_0DViewer_CookbookPymeasure

RECIPES = {
    'serial': (DAQ_Move_CookbookSerial, DAQ_0DViewer_CookbookSerial),
    'visa': (DAQ_Move_CookbookVisa, DAQ_0DViewer_CookbookVisa),
    'pymeasure': (DAQ_Move_CookbookPymeasure, DAQ_0DViewer_CookbookPymeasure),
}


@pytest.fixture(params=list(RECIPES))
def recipe(request):
    return RECIPES[request.param]


@pytest.fixture
def actuator(qapp, recipe):
    plugin = make_actuator(recipe[0])
    assert plugin.initialized
    yield plugin
    plugin.close()


class TestActuator:
    def test_ini_returns_the_identity(self, actuator):
        assert 'CookbookDevice' in actuator.init_info

    def test_value_has_units(self, actuator):
        assert actuator.get_actuator_value().units == 'mm'

    def test_move_abs(self, actuator):
        pos = move_abs_and_wait(actuator, 2.5)
        assert pos.value('mm') == pytest.approx(2.5, abs=0.01)

    def test_move_rel(self, actuator):
        move_abs_and_wait(actuator, 1.)
        pos = move_rel_and_wait(actuator, 0.5)
        assert pos.value('mm') == pytest.approx(1.5, abs=0.01)

    def test_move_home(self, actuator):
        move_abs_and_wait(actuator, 3.)
        pos = move_home_and_wait(actuator)
        assert pos.value('mm') == pytest.approx(0., abs=0.01)

    def test_close_releases_the_controller(self, qapp, recipe):
        plugin = make_actuator(recipe[0])
        controller = plugin.controller
        plugin.close()
        # closing twice must be harmless
        plugin.close()
        assert controller is not None


class TestDetector:
    def test_grab_returns_a_voltage(self, qapp, recipe):
        detector = make_detector(recipe[1])
        try:
            dte = grab_and_wait(detector)
            assert dte[0].shape == (1,)
            assert_units(dte, 'V')
            assert dte[0].data[0][0] == pytest.approx(0.5, abs=0.01)  # the stage is at 0
        finally:
            detector.close()


def test_detector_shares_the_controller_of_the_actuator(qapp, recipe):
    """Same controller ID in the Dashboard: the actuator is the master, the detector its slave"""
    actuator = make_actuator(recipe[0])
    detector = make_detector(recipe[1], controller=actuator.controller)
    try:
        assert detector.controller is actuator.controller
        move_abs_and_wait(actuator, 2.)
        dte = grab_and_wait(detector)
        assert dte[0].data[0][0] == pytest.approx(0.5 + 0.1 * 2., abs=0.01)
        detector.close()  # a slave never closes the shared controller
        assert actuator.get_actuator_value().value('mm') == pytest.approx(2., abs=0.01)
    finally:
        actuator.close()
