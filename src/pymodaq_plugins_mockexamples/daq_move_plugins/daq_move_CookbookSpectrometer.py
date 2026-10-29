"""Cookbook recipe 3b: actuator that is a slave of a detector: the grating of a spectrometer (central wavelength).

COPY this file for an actuator that is one function of an instrument mostly used as a detector: the grating of a
spectrometer, the focus of a camera, the filter wheel of a detector...
ADAPT: ``params``, ``ini_stage`` and the calls of the driver in ``move_abs``, ``move_rel``, ``move_home``,
``stop_motion`` and ``get_actuator_value``.
KEEP:
- the master/slave handling in ``ini_stage`` and ``close``: alone the actuator owns the instrument, with the same
  controller ID as the detector ``CookbookSpectrometer`` it shares the instrument of the master;
- ``user_condition_to_reach_target``: the grating takes time, so the end of the move is read from the instrument;
- ``move_home``: the homing is not polled by PyMoDAQ, so the plugin waits for its end and calls ``move_done``.

Moving the grating changes the wavelength axis of the detector, see ``daq_1Dviewer_CookbookSpectrometer.py``.

Who runs where (GUI thread, plugin thread, driver thread): see the diagrams of "How an instrument plugin works with the
Dashboard" (``plugin_workflow``) in the developer guide of PyMoDAQ.
"""
from qtpy.QtCore import QThread

from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, DataActuatorType,
                                                          DataActuator, main)

from pymodaq_plugins_mockexamples.hardware.spectrometer import Spectrometer


class DAQ_Move_CookbookSpectrometer(DAQ_Move_base):
    """Central wavelength of the simulated spectrometer"""
    _controller_units = 'nm'
    is_multiaxes = False
    _epsilons = 0.1
    data_actuator_type = DataActuatorType.DataActuator
    params = comon_parameters_fun(is_multiaxes, epsilon=_epsilons)

    def ini_attributes(self):
        self.controller: Spectrometer = None

    def ini_stage(self, controller=None):
        if self.is_master:
            self.controller = Spectrometer()
        else:  # a master detector shares its instrument
            self.controller = controller
        return self.controller.infos, True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.close()

    def user_condition_to_reach_target(self) -> bool:
        return not self.controller.moving

    def get_actuator_value(self) -> DataActuator:
        position = DataActuator(data=self.controller.get_wavelength(), units=self.axis_unit)
        return self.get_position_with_scaling(position)

    def move_abs(self, value: DataActuator):
        value = self.check_bound(value)
        self.target_value = value
        value = self.set_position_with_scaling(value)
        self.controller.set_wavelength(value.value(self.axis_unit))

    def move_rel(self, value: DataActuator):
        value = self.check_bound(self.current_value + value) - self.current_value
        self.target_value = value + self.current_value
        value = self.set_position_with_scaling(self.target_value)
        self.controller.set_wavelength(value.value(self.axis_unit))

    def move_home(self):
        self.controller.find_reference()
        while self.controller.moving:  # PyMoDAQ does not poll the position after a home: wait for the end here
            QThread.msleep(20)
        self.move_done()

    def stop_motion(self):
        self.controller.stop()

    def commit_settings(self, param):
        pass


if __name__ == '__main__':
    main(__file__)
