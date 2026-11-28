"""A simulated absorption bench: a lamp, a beam block, a cuvette holder and one spectrometer

What the spectrometer measures depends on the two actuators of the bench, as on a real one:

* the beam block (1: the light is blocked, the spectrometer sees only its dark level; 0: the beam goes through)
* the cuvette holder (0: the blank cuvette, the spectrometer sees the lamp; 1: the cuvette with the sample, which
  absorbs around 550 nm: its transmittance is about 0.9 away from the band and 0.2 at its centre)

Used by the plugins ``MockBeamBlock``, ``MockSampleChanger`` (actuators) and ``MockSpectro`` (the spectrometer) of the
ontology demo, as in the experiments ``spectro_lab_a`` and ``spectro_lab_b``. The three modules share the one bench of the
process (:meth:`SpectroBench.shared`): it is a simulation, a real bench would be one controller shared by its modules.
"""
import numpy as np

WAVELENGTHS = np.linspace(400., 800., 400)  # nm
DARK_LEVEL = 100.  # counts
LAMP_MAX = 20000.  # counts at the maximum of the lamp spectrum


def lamp_spectrum() -> np.ndarray:
    """Counts of the lamp alone, without the dark level"""
    return LAMP_MAX * np.exp(-((WAVELENGTHS - 600.) / 200.) ** 2)


def transmittance_of_sample() -> np.ndarray:
    """Fraction of the light that goes through the sample"""
    return 0.9 - 0.7 * np.exp(-((WAVELENGTHS - 550.) / 30.) ** 2)


class SpectroBench:
    """The bench: set ``beam_block`` and ``sample_position``, then read a spectrum, in counts, with a little noise"""

    _shared: 'SpectroBench' = None

    @classmethod
    def shared(cls) -> 'SpectroBench':
        """The bench used by all the modules of the process"""
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    def __init__(self):
        self.beam_block = 0.  # 1: the beam is blocked
        self.sample_position = 0.  # 1: the cuvette with the sample is in the beam, 0: the blank one
        self._rng = np.random.default_rng()

    def get_wavelength_axis(self) -> np.ndarray:
        return WAVELENGTHS.copy()

    def grab_spectrum(self) -> np.ndarray:
        if self.beam_block >= 0.5:
            signal = np.zeros_like(WAVELENGTHS)
        elif self.sample_position >= 0.5:
            signal = lamp_spectrum() * transmittance_of_sample()
        else:
            signal = lamp_spectrum()
        counts = DARK_LEVEL + signal
        return counts + self._rng.normal(0., 1., counts.shape) * np.sqrt(counts) * 0.2

    def close(self) -> None:
        pass
