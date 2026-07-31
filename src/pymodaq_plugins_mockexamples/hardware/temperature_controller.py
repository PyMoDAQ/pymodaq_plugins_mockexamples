from time import perf_counter

from qtpy.QtCore import QTimer, QObject

from numpy.random import random
import numpy as np
from pymodaq import Q_

from simple_pid import PID


class TempController(QObject):
    """ Simulation fo a temperature controller with inner PID stabilization loop

    Can be enabled or disabled. In that last case, the power can be set manually
    """
    has_cooling = False # whether the setup has the power to cool on top of heating

    def __init__(self, kp=0.1, ki=0., kd=0.):
        super().__init__()
        self._current_power = 0.
        self._ellapsed_time = 0.0
        self._current_temperature = 299.
        self._ambiant_temperature = 299.
        self._instantaneous_temperature = self._current_temperature
        self._noise = 0.1

        self.pid_timer = QTimer()
        self.pid_timer.timeout.connect(self.update_temperature)
        self.pid_timer.setInterval(10)


        self.pid = PID(kp, ki, kd, setpoint=self._ambiant_temperature, auto_mode=False)
        self.pid_timer.start()

    def enable(self, do_enable=True):
        """ Enable or disable the PID controller """
        self.pid.set_auto_mode(do_enable, last_output=self._current_power)

    def reset(self):
        """ Reset the PID controller: constants and history """
        self.pid.reset()

    def close(self):
        """ Terminate the program"""
        self.pid_timer.stop()

    @property
    def kp(self):
        """ Get/Set the proportional constant of the PID controller """
        return self.pid.Kp

    @kp.setter
    def kp(self, value: float):
        self.pid.Kp = value

    @property
    def ki(self):
        """ Get/Set the integral constant of the PID controller """
        return self.pid.Ki

    @ki.setter
    def ki(self, value: float):
        self.pid.Ki = value

    @property
    def kd(self):
        """ Get/Set the derivative constant of the PID controller """
        return self.pid.Kd

    @kd.setter
    def kd(self, value: float):
        self.pid.Kd = value

    def update_temperature(self):
        """ inner method called periodically by a timer to compute the temperature and the eventual correction to be
        applied as calculated by the PID"""

        dt = perf_counter() - self._ellapsed_time
        self._ellapsed_time  = perf_counter()

        self._current_temperature += 1 * self._current_power * dt + self._noise * (random() - 0.5)
        self._instantaneous_temperature = self._current_temperature

        # some heat dissipation
        self._current_temperature -= 0.2 * dt
        #not below ambiant
        self._current_temperature = np.clip(self._current_temperature, self.ambiant_temp, None)

        if self.pid.auto_mode:
            if self.has_cooling:
                self._current_power = self.pid(self._current_temperature)
            else:
                self._current_power = np.clip(self.pid(self._current_temperature), 0., None)

    @property
    def power(self) -> Q_:
        """ Get/set the power currently  applied to the system

        Manually setting its value is only possible when the pid is disabled
        """
        return Q_(self._current_power, 'W')

    @power.setter
    def power(self, value: Q_ | float):
        if isinstance(value, float):
            value = Q_(value, 'W')
        if not self.pid.auto_mode:
            self._current_power = value.m_as('W')

    @property
    def temperature(self):
        """ Get the current temperature."""
        return self._instantaneous_temperature

    @property
    def target_temperature(self):
        """ Get/set the pid target temperature"""
        return self.pid.setpoint

    @target_temperature.setter
    def target_temperature(self, value: float):
        self.pid.setpoint = value

    @property
    def ambiant_temp(self):
        """ Get/set the ambient temperature"""
        return self._ambiant_temperature

    @ambiant_temp.setter
    def ambiant_temp(self, temperature):
        self._ambiant_temperature = temperature

    @property
    def noise(self):
        """Get/set the noise level"""
        return self._noise

    @noise.setter
    def noise(self, noise):
        self._noise = noise


