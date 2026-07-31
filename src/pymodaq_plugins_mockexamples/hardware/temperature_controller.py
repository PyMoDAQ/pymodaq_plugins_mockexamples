from time import perf_counter

from qtpy.QtCore import QTimer, QObject

from numpy.random import random
import numpy as np
from pymodaq import Q_

from simple_pid import PID


class TempController(QObject):
    has_cooling = False

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
        self.pid_timer.setInterval(50)

        self.pid = PID(kp, ki, kd, setpoint=self._ambiant_temperature)

        self.pid_timer.start()

    def pause(self, do_pause=True):
        self.pid.set_auto_mode(do_pause, last_output=self._current_power)

    @property
    def kp(self):
        return self.pid.Kp

    @kp.setter
    def kp(self, value: float):
        self.pid.Kp = value

    @property
    def ki(self):
        return self.pid.Ki

    @ki.setter
    def ki(self, value: float):
        self.pid.Ki = value

    @property
    def kd(self):
        return self.pid.Kd

    @kd.setter
    def kd(self, value: float):
        self.pid.Kd = value

    def update_temperature(self):
        dt = perf_counter() - self._ellapsed_time
        self._ellapsed_time  = perf_counter()

        self._current_temperature += 1 * self._current_power * dt + self._noise * (random() - 0.5)
        self._instantaneous_temperature = self._current_temperature

        # some heat dissipation
        self._current_temperature -= 0.2 * dt
        #not below ambiant
        self._current_temperature = np.clip(self._current_temperature, self.ambiant_temp, None)

        if self.has_cooling:
            self._current_power = self.pid(self._current_temperature)
        else:
            self._current_power = np.clip(self.pid(self._current_temperature), 0., None)

    @property
    def temperature(self):
        return self._instantaneous_temperature

    @temperature.setter
    def temperature(self, value: float):
        self.pid.setpoint = value

    @property
    def target_temperature(self):
        return self.pid.setpoint

    @property
    def ambiant_temp(self):
        return self._ambiant_temperature

    @ambiant_temp.setter
    def ambiant_temp(self, temperature):
        self._ambiant_temperature = temperature

    @property
    def noise(self):
        return self._noise

    @noise.setter
    def noise(self, noise):
        self._noise = noise

    def reset(self):
        self.pid.reset()
