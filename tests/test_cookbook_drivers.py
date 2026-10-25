"""Tests of the drivers of the cookbook recipes, without PyMoDAQ: against the simulated device, and for pymeasure
against a scripted ``ProtocolAdapter`` that checks the exact commands."""
import time

import pytest
from pymeasure.adapters import ProtocolAdapter

from pymodaq_plugins_mockexamples.hardware.fake_instrument import (FakeInstrument, FakeSerialPort, FakeVisaResource)
from pymodaq_plugins_mockexamples.hardware.pymeasure_source import CookbookSource, MockAdapter
from pymodaq_plugins_mockexamples.hardware.serial_stage import SerialStage, SerialStageError
from pymodaq_plugins_mockexamples.hardware.visa_meter import VisaMeter, VisaMeterError


@pytest.fixture(params=['serial', 'visa'])
def direct_driver(request):
    """The two drivers written directly on a port have the same public methods: the same tests apply"""
    device = FakeInstrument(speed=1000.)
    if request.param == 'serial':
        driver = SerialStage(FakeSerialPort(device))
    else:
        driver = VisaMeter(FakeVisaResource(device))
    yield driver, device
    driver.close()


class TestDirectDrivers:
    def test_identity(self, direct_driver):
        driver, _ = direct_driver
        assert driver.identity() == FakeInstrument.IDN

    def test_move_and_read_back(self, direct_driver):
        driver, _ = direct_driver
        driver.move_to(5.)
        time.sleep(0.02)
        assert driver.position == pytest.approx(5., abs=1e-3)
        assert driver.read_voltage() == pytest.approx(0.5 + 0.1 * 5., abs=1e-3)

    def test_home_waits_for_the_stage(self, direct_driver):
        driver, _ = direct_driver
        driver.move_to(3.)
        time.sleep(0.01)
        driver.home()
        assert abs(driver.position) < 0.01

    def test_stop_keeps_the_stage_where_it_is(self, direct_driver):
        driver, device = direct_driver
        device.speed = 10.
        driver.move_to(50.)
        time.sleep(0.05)
        driver.stop()
        stopped_at = driver.position
        time.sleep(0.05)
        assert 0. < stopped_at < 50.
        assert driver.position == pytest.approx(stopped_at, abs=1e-3)

    def test_device_errors_are_raised(self, direct_driver):
        driver, device = direct_driver
        device.execute('NOT A COMMAND')
        with pytest.raises(SerialStageError if isinstance(driver, SerialStage) else VisaMeterError):
            driver.check_error()

    def test_close_twice(self, direct_driver):
        driver, _ = direct_driver
        driver.close()
        driver.close()


def test_serial_no_answer_is_a_timeout_error():
    port = FakeSerialPort()
    port.write = lambda data: len(data)  # a device that never answers
    with pytest.raises(SerialStageError, match='No answer'):
        SerialStage(port).identity()


def test_serial_commands_are_terminated():
    device = FakeInstrument()
    SerialStage(FakeSerialPort(device)).move_to(1.5)
    assert device.commands == ['POS 1.5000', 'SYST:ERR?']


class TestPymeasureDriver:
    def test_commands_sent_and_answers_read(self):
        adapter = ProtocolAdapter([
            ('POS 2.5', None), ('SYST:ERR?', '0,"No error"'),
            ('POS?', '2.5'),
            ('MEAS:VOLT?', '0.75'),
            ('HOME', None),
        ])
        source = CookbookSource(adapter)
        source.position = 2.5
        assert source.position == 2.5
        assert source.voltage == 0.75
        source.home()

    def test_out_of_range_is_refused_before_sending(self):
        adapter = ProtocolAdapter([])
        with pytest.raises(ValueError):
            CookbookSource(adapter).position = 500.

    def test_against_the_simulated_device(self):
        source = CookbookSource(MockAdapter(FakeInstrument(speed=1000.)))
        assert source.id == FakeInstrument.IDN
        source.position = 4.
        time.sleep(0.02)
        assert source.position == pytest.approx(4., abs=1e-3)
        assert source.voltage == pytest.approx(0.9, abs=1e-3)
        source.check_errors()
