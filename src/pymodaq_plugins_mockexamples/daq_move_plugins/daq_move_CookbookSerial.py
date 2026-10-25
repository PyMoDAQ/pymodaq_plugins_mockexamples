"""Cookbook recipe 1a: actuator on a serial line, with a driver written directly on the port.

COPY this file for an actuator controlled through a serial port (RS-232, USB-serial) with a text protocol.
ADAPT: ``params`` (connection settings), ``ini_stage`` (how the controller is created), ``_controller_units``, the
axis name and epsilon, and the driver calls of ``move_abs``, ``move_rel``, ``get_actuator_value``, ``move_home`` and
``stop_motion``.
KEEP: the structure of the methods, the master/slave handling in ``ini_stage`` and ``close``, and the call of
``move_done`` at the end of ``move_home``.

Try it without hardware: leave the port to ``MOCK``, the stage is then the simulated device of
``hardware/mock_serial_visa_instrument.py``. Give the same controller ID in the Dashboard to this actuator and to the detector
``CookbookSerial`` to make them share the driver. See ``hardware/serial_stage.py`` for the driver and
``tests/test_cookbook_drivers.py`` and ``tests/test_cookbook_plugins.py`` for the tests.
"""
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, DataActuatorType,
                                                          DataActuator, main)

from pymodaq_plugins_mockexamples.hardware.mock_serial_visa_instrument import MockSerialPort
from pymodaq_plugins_mockexamples.hardware.serial_stage import SerialStage


class DAQ_Move_CookbookSerial(DAQ_Move_base):
    """Stage of the simulated device, driven through ``SerialStage`` on a serial port"""
    _controller_units = 'mm'
    is_multiaxes = False
    _axis_names = ['position']
    _epsilons = [0.01]
    data_actuator_type = DataActuatorType.DataActuator
    params = comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilons) + [
        {'title': 'Serial port:', 'name': 'port', 'type': 'str', 'value': 'MOCK',
         'tip': 'Name of the serial port (COM3, /dev/ttyUSB0), MOCK for the simulated device'},
        {'title': 'Baudrate:', 'name': 'baudrate', 'type': 'int', 'value': 9600},
    ]

    def ini_attributes(self):
        self.controller: SerialStage = None

    def ini_stage(self, controller=None):
        if self.is_master:
            port = MockSerialPort() if self.settings['port'] == 'MOCK' else self.settings['port']
            self.controller = SerialStage(port, baudrate=self.settings['baudrate'])
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
