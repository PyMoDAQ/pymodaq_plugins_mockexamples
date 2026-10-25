"""Cookbook recipe 3a (recommended for text protocols): actuator driven through a ``pymeasure`` instrument.

COPY this file for an actuator whose instrument has, or deserves, a ``pymeasure`` driver. The driver does the
protocol work (``hardware/pymeasure_source.py``), so the plugin is only the translation between PyMoDAQ and the
properties of the driver.
ADAPT: ``params``, ``ini_stage`` (the adapter and the driver class), ``_controller_units``, axis name and epsilon, and
the names of the driver properties used in the methods.
KEEP: the structure of the methods, the master/slave handling in ``ini_stage`` and ``close``, and the call of
``move_done`` at the end of ``move_home``.
ERRORS: ``@report_errors`` shows the error of the driver in the status bar of the module, as PyMoDAQ only logs an
exception raised by a plugin method; keep it on the methods that call the driver.

Try it without hardware: leave the address to ``MOCK``. Give the same controller ID to this actuator and to the
detector ``CookbookPymeasure`` to make them share the driver. See ``tests/test_cookbook_drivers.py`` and ``tests/test_cookbook_plugins.py`` for the tests.
"""
import time

from pymeasure.adapters import VISAAdapter

from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, DataActuatorType,
                                                          DataActuator, main)

from pymodaq_plugins_mockexamples.hardware.pymeasure_source import CookbookSource, MockAdapter
from pymodaq_plugins_mockexamples.utils import report_errors


class DAQ_Move_CookbookPymeasure(DAQ_Move_base):
    """Stage of the simulated device, driven through the pymeasure instrument ``CookbookSource``"""
    _controller_units = 'mm'
    is_multiaxes = False
    _axis_names = ['position']
    _epsilons = [0.01]
    data_actuator_type = DataActuatorType.DataActuator
    params = comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilons) + [
        {'title': 'VISA address:', 'name': 'address', 'type': 'str', 'value': 'MOCK',
         'tip': 'VISA resource, for instance TCPIP0::192.168.0.5::INSTR, MOCK for the simulated device'},
    ]

    def ini_attributes(self):
        self.controller: CookbookSource = None

    def ini_stage(self, controller=None):
        if self.is_master:
            address = self.settings['address']
            self.controller = CookbookSource(MockAdapter() if address == 'MOCK' else VISAAdapter(address))
        else:  # a master detector or actuator shares its controller
            self.controller = controller
        return self.controller.id, True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.adapter.close()

    def get_actuator_value(self) -> DataActuator:
        position = DataActuator(data=self.controller.position, units=self.axis_unit)
        return self.get_position_with_scaling(position)

    @report_errors
    def move_abs(self, value: DataActuator):
        value = self.check_bound(value)
        self.target_value = value
        value = self.set_position_with_scaling(value)
        self.controller.position = value.value(self.axis_unit)  # validated by the driver, then sent

    @report_errors
    def move_rel(self, value: DataActuator):
        value = self.check_bound(self.current_value + value) - self.current_value
        self.target_value = value + self.current_value
        value = self.set_position_with_scaling(self.target_value)
        self.controller.position = value.value(self.axis_unit)

    @report_errors
    def move_home(self):
        self.controller.home()
        t_end = time.monotonic() + 10.
        while abs(self.controller.position) > 0.005 and time.monotonic() < t_end:  # blocking homing
            time.sleep(0.01)
        self.move_done()  # PyMoDAQ does not poll the position after a home

    @report_errors
    def stop_motion(self):
        self.controller.stop()

    def commit_settings(self, param):
        pass


if __name__ == '__main__':
    main(__file__)
