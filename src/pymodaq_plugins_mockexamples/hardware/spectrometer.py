"""A simulated grating spectrometer: a grating that turns to set the central wavelength, and a spectrum on a sensor.

Adapted from the spectrometer of ``pymodaq_plugins_teaching`` (module A of the teaching experiments).
"""
import math
from time import perf_counter

import numpy as np

from pymodaq_utils.math_utils import gauss1D


class Spectrometer:
    """Simulated spectrometer

    The grating can be changed, turned to set the central wavelength (it takes time, as a real one) and the
    spectrum is read from a sensor of ``Nx`` pixels. The wavelength of each pixel depends on the central wavelength
    and on the dispersion of the grating: this calibration axis is what the plugin sends with the data.
    """
    gratings = {'G300': 0.7, 'G1200': 0.25}  # name: dispersion in nm/pixel
    Nx = 256  # pixels of the sensor
    infos = 'Spectrometer simulator'
    _epsilon = 0.01  # nm, the grating is considered at its target below that distance
    reference_exposure_ms = 100.  # the exposure at which the amplitude of the line is ``amp``

    def __init__(self):
        self._amp = 10.
        self._noise = 0.5
        self._width = 2.  # nm
        self._grating = next(iter(self.gratings))
        self._tau = 0.5  # s, characteristic time of the grating to reach its target
        self._lambda = 532.  # nm, central wavelength
        self._target_lambda = self._lambda
        self._init_value = self._lambda
        self._alpha = 0.
        self._start_time = 0.
        self._moving = False
        self._peak_wavelength = 528.  # nm, the line that is measured
        self.exposure_ms = self.reference_exposure_ms

    def close(self):
        self.stop()

    @property
    def tau(self) -> float:
        """Characteristic time (s) taken by the grating to reach a wavelength"""
        return self._tau

    @tau.setter
    def tau(self, value: float):
        if value <= 0:
            raise ValueError(f'A characteristic time of {value} is not possible. It should be strictly positive')
        self._tau = value

    @property
    def grating(self) -> str:
        return self._grating

    @grating.setter
    def grating(self, name: str):
        if name not in self.gratings:
            raise ValueError(f'Unknown grating {name}, use one of {list(self.gratings)}')
        self._grating = name

    @property
    def dispersion(self) -> float:
        """Wavelength range (nm) of one pixel of the sensor with the current grating"""
        return self.gratings[self._grating]

    @property
    def peak_wavelength(self) -> float:
        """Wavelength (nm) of the line that is measured"""
        return self._peak_wavelength

    @peak_wavelength.setter
    def peak_wavelength(self, value: float):
        self._peak_wavelength = value

    @property
    def moving(self) -> bool:
        self.get_wavelength()
        return self._moving

    def stop(self):
        self.get_wavelength()
        self._moving = False

    def find_reference(self):
        """Turn the grating to a known position, for absolute positioning"""
        self.set_wavelength(600.)

    def set_wavelength(self, value: float, relative: bool = False):
        """Start turning the grating to set the central wavelength (nm)"""
        target = self._lambda + value if relative else value
        if target < 0:
            raise ValueError('Wavelength cannot be negative')
        self._init_value = self.get_wavelength()
        self._target_lambda = target
        distance = math.fabs(self._init_value - target)
        self._alpha = math.fabs(math.log(self._epsilon / max(distance, 10 * self._epsilon)))
        self._start_time = perf_counter()
        self._moving = True

    def get_wavelength(self) -> float:
        """Current central wavelength (nm): it approaches the target exponentially while the grating turns"""
        if self._moving:
            decay = math.exp(-self._alpha * (perf_counter() - self._start_time) / self._tau)
            self._lambda = decay * (self._init_value - self._target_lambda) + self._target_lambda
            if math.fabs(self._lambda - self._target_lambda) < self._epsilon:
                self._lambda = self._target_lambda
                self._moving = False
        return self._lambda

    def get_wavelength_axis(self) -> np.ndarray:
        """Wavelength (nm) of each pixel: centred on the central wavelength, spaced by the dispersion"""
        return (np.arange(self.Nx) - self.Nx / 2) * self.dispersion + self.get_wavelength()

    def grab_spectrum(self) -> np.ndarray:
        """Intensity on each pixel: one line and some noise"""
        wavelengths = self.get_wavelength_axis()
        return (self.exposure_ms / self.reference_exposure_ms
                * (self._amp * gauss1D(wavelengths, self._peak_wavelength, self._width)
                   + self._noise * np.random.rand(self.Nx)))
