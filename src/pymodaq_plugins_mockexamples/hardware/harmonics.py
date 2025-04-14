import numpy as np

from pymodaq_utils import math_utils as mutils
from pymodaq_utils.units import nm2eV, eV2nm

from pymodaq_data import Q_
from pymodaq_plugins_mock.hardware.wrapper import ActuatorWrapperWithTauMultiAxes


class Harmonics(ActuatorWrapperWithTauMultiAxes):
    axes = ['Power']
    _units = ['W']
    units = _units
    epsilons = [0.001]  # the precision is therefore 1 µm, 1e-4 mm and 1°
    _tau = 0.5  # in s

    def __init__(self):
        super().__init__()
        self._current_values = [1. for _ in self.axes]
        self._n_harmonics = 3
        self._omega0 = Q_(nm2eV(800), 'eV')
        self._omega_noise = Q_(0.2, 'eV')
        self._domega_ev = Q_(0.2, 'eV')
        self._npts = 512
        self._current_value = 1.0
        self._target_value = 1.0

    @property
    def amplitude(self) -> float:
        return self.get_value('Power')

    @amplitude.setter
    def amplitude(self, amp: float):
        self.move_at(amp, 'Power')

    @property
    def power(self) -> Q_:
        return Q_(self.amplitude, self.units[0])

    @property
    def omega_noise(self):
        return self._omega_noise

    @omega_noise.setter
    def omega_noise(self, omega_eV: float):
        self._omega_noise = Q_(omega_eV, 'eV')

    @property
    def n_harmonics(self) -> int:
        return self._n_harmonics

    @n_harmonics.setter
    def n_harmonics(self, nhar: int):
        if isinstance(nhar, int):
            self._n_harmonics = nhar

    def get_axis(self) -> Q_:
        return np.linspace(0, (self._n_harmonics + 1) * self._omega0, self._npts)

    def get_spectrum(self) -> Q_:
        axis = self.get_axis()
        spectrum = Q_(np.zeros((self._npts,)))
        omega_noise = self._omega_noise * (np.random.random() * 2 - 1)
        for ind in range(self._n_harmonics):
            spectrum += mutils.gauss1D(axis,
                                       (1 + ind) * self._omega0 + omega_noise,
                                       self._domega_ev)
        spectrum *= self._current_values[0]
        spectrum += 0.1 * np.random.random_sample((self._npts,))
        spectrum *= mutils.gauss1D(axis, self._omega0, self.n_harmonics * self._omega0 * 2 / 3)
        return spectrum
