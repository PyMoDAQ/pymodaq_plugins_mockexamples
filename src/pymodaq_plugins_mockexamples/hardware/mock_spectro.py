"""A simulated spectrophotometer measuring, in counts, the dark, the lamp (reference) or the lamp through a sample

The sample absorbs around 550 nm: its transmittance is about 0.9 away from the band and drops to 0.2 at the centre.
Used by the plugins ``MockSpectroDark``, ``MockSpectroReference`` and ``MockSpectroSample`` of the ontology demo.
"""
import numpy as np

KINDS = ('dark', 'reference', 'sample')
WAVELENGTHS = np.linspace(400., 800., 400)  # nm
DARK_LEVEL = 100.  # counts
LAMP_MAX = 20000.  # counts at the maximum of the lamp spectrum


def lamp_spectrum() -> np.ndarray:
    """Counts of the lamp alone, without the dark level"""
    return LAMP_MAX * np.exp(-((WAVELENGTHS - 600.) / 200.) ** 2)


def transmittance_of_sample() -> np.ndarray:
    """Fraction of the light that goes through the sample"""
    return 0.9 - 0.7 * np.exp(-((WAVELENGTHS - 550.) / 30.) ** 2)


class MockSpectro:
    """Spectra in counts of the kind asked ('dark', 'reference' or 'sample'), with a little noise"""

    def __init__(self, kind: str):
        if kind not in KINDS:
            raise ValueError(f'kind must be one of {KINDS}, not {kind}')
        self.kind = kind
        self._rng = np.random.default_rng()

    def get_wavelength_axis(self) -> np.ndarray:
        return WAVELENGTHS.copy()

    def grab_spectrum(self) -> np.ndarray:
        signal = {'dark': np.zeros_like(WAVELENGTHS), 'reference': lamp_spectrum(),
                  'sample': lamp_spectrum() * transmittance_of_sample()}[self.kind]
        counts = DARK_LEVEL + signal
        return counts + self._rng.normal(0., 1., counts.shape) * np.sqrt(counts) * 0.2

    def close(self) -> None:
        pass
