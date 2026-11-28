"""Ontology demo: the spectrometer of a simulated absorption bench, in counts on a wavelength axis in nm

What it sees depends on the beam block (``MockBeamBlock``) and on the cuvette holder (``MockSampleChanger``), which
share the same simulated bench (``hardware/spectro_bench.py``). The module has a
neutral name in the experiments ``spectro_lab_a`` and ``spectro_lab_b``: what a spectrum means depends on the state of
the bench when it is taken, which is what the ontology describes.
"""
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins, Axis
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.spectro_bench import SpectroBench


class DAQ_1DViewer_MockSpectro(DAQ_Viewer_base):
    """Counts of the spectrometer of the bench, on a wavelength axis in nm"""
    params = comon_parameters

    def ini_attributes(self):
        self.controller: SpectroBench = None

    def ini_detector(self, controller=None):
        self.controller = SpectroBench.shared()
        return 'Simulated spectrometer', True

    def close(self):
        pass

    def commit_settings(self, param):
        pass

    def grab_data(self, Naverage=1, **kwargs):
        axis = Axis(data=self.controller.get_wavelength_axis(), label='wavelength', units='nm', index=0)
        n = max(Naverage, 1)
        spectrum = sum(self.controller.grab_spectrum() for _ in range(n)) / n
        self.dte_signal.emit(DataToExport(
            name='MockSpectro',
            data=[DataFromPlugins(name='Spectrum', data=[spectrum], dim='Data1D', labels=['intensity'],
                                  units='counts', axes=[axis])]))

    def stop(self):
        pass


if __name__ == '__main__':
    main(__file__)
