from time import perf_counter

from qtpy.QtCore import QTimer, QObject

from numpy.random import random
import numpy as np
from pymodaq import Q_

from simple_pid import PID


class HeaterController(QObject):
    _current_temperature = 20.
    _ambiant_temperature = 19.
    _noise = 0.1

    def __init__(self, ):
        super().__init__()
        self._current_power = 0.
        self._ellapsed_time = Q_(0., 's')
        self._target_temperature = self._ambiant_temperature
        self._tau = Q_(1, 's')

        self.pid_timer = QTimer()


    def update_temperature(self):
        dt = Q_(perf_counter(), 's') - self._ellapsed_time
        self._ellapsed_time += dt

        self._current_temperature += 1 * self._current_power * dt.m_as('s') + self._noise * (random() - 0.5)
        # some heat dissipation
        self._current_temperature -= 0.2 * dt.m_as('s')
        self._current_temperature = np.clip(self._current_temperature, self.ambiant_temp, None)

    @property
    def temperature(self):
        return self._current_temperature

    @temperature.setter
    def temperature(self, value):
        self._target_temperature = value

    def check_position(self):
        return self._current_power

    def move_abs(self, value):
        self._current_power = value

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

    def move_rel(self, value):
        self._current_power += value

    def grab(self):
        return self._current_temperature



