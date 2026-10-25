"""Cookbook recipe 2a: actuator on a VISA resource, with a driver written directly on pyvisa.

COPY this file for an actuator controlled through VISA (GPIB, USB-TMC, TCP/IP, serial) with SCPI commands.
ADAPT: ``params`` (connection settings), ``ini_stage`` (how the controller is created), ``_controller_units``, the
axis name and epsilon, and the driver calls of ``move_abs``, ``move_rel``, ``get_actuator_value``, ``move_home`` and
``stop_motion``.
KEEP: the structure of the methods, the master/slave handling in ``ini_stage`` and ``close``, and the call of
``move_done`` at the end of ``move_home``.

Try it without hardware: leave the address to ``MOCK``, the stage is then the simulated device of
``hardware/mock_instrument.py``. Give the same controller ID in the Dashboard to this actuator and to the detector
``CookbookVisa`` to make them share the driver. See ``hardware/visa_meter.py`` for the driver and
``tests/test_cookbook_drivers.py`` and ``tests/test_cookbook_plugins.py`` for the tests.
"""
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, DataActuatorType,
                                                          DataActuator, main)

from pymodaq_plugins_mockexamples.hardware.mock_instrument import MockVisaResource
from pymodaq_plugins_mockexamples.hardware.visa_meter import VisaMeter


class DAQ_Move_CookbookVisa(DAQ_Move_base):
    """Stage of the simulated device, driven through ``VisaMeter`` on a VISA resource"""
    _controller_units = 'mm'
    is_multiaxes = False
    _axis_names = ['position']
    _epsilons = [0.01]
    data_actuator_type = DataActuatorType.DataActuator
    params = comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilons) + [
        {'title': 'VISA address:', 'name': 'address', 'type': 'str', 'value': 'MOCK',
         'tip': 'VISA resource, for instance TCPIP0::192.168.0.5::INSTR, MOCK for the simulated device'},
        {'title': 'Timeout (ms):', 'name': 'visa_timeout', 'type': 'int', 'value': 2000},
    ]

    def ini_attributes(self):
        self.controller: VisaMeter = None

    def ini_stage(self, controller=None):
        if self.is_master:
            address = self.settings['address']
            self.controller = VisaMeter(MockVisaResource() if address == 'MOCK' else address,
                                        timeout=self.settings['visa_timeout'])
        else:  # a master detector or actuator shares its controller
            self.controller = controller
        return self.controller.identity(), True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.close()

    def get_actuator_value(self) -> DataActuator:
        position = DataActuator(data=self.controller.position, units=self.axis_unit)
        return self.get_position_with_scaling(position)

    def move_abs(self, value: DataActuator):
        value = self.check_bound(value)
        self.target_value = value
        value = self.set_position_with_scaling(value)
        self.controller.move_to(value.value(self.axis_unit))

    def move_rel(self, value: DataActuator):
        value = self.check_bound(self.current_value + value) - self.current_value
        self.target_value = value + self.current_value
        value = self.set_position_with_scaling(self.target_value)
        self.controller.move_to(value.value(self.axis_unit))

    def move_home(self):
        self.controller.home()
        self.move_done()  # the homing is blocking here, and PyMoDAQ does not poll the position after a home

    def stop_motion(self):
        self.controller.stop()

    def commit_settings(self, param):
        pass


if __name__ == '__main__':
    main(__file__)
