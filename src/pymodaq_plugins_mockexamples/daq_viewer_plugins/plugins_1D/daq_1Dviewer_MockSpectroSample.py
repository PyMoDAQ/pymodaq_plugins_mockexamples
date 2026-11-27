"""Ontology demo: a simulated spectrometer looking at the lamp through a sample (the spectrum is in counts)

The three plugins ``MockSpectroDark``, ``MockSpectroReference`` and ``MockSpectroSample`` are the same instrument
measuring a different thing. In the Dashboard the modules are given neutral names (experiments ``spectro_lab_a`` and
``spectro_lab_b``): it is the term assigned in the ontology manager that tells what each one measures.
"""
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins, Axis
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.mock_spectro import MockSpectro


class DAQ_1DViewer_MockSpectroSample(DAQ_Viewer_base):
    """Counts of the lamp through the sample, on a wavelength axis in nm"""
    kind = 'sample'
    params = comon_parameters

    def ini_attributes(self):
        self.controller: MockSpectro = None

    def ini_detector(self, controller=None):
        self.controller = MockSpectro(self.kind) if self.is_master else controller
        return f'Simulated spectrometer ({self.kind})', True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.close()

    def commit_settings(self, param):
        pass

    def grab_data(self, Naverage=1, **kwargs):
        axis = Axis(data=self.controller.get_wavelength_axis(), label='wavelength', units='nm', index=0)
        spectrum = sum(self.controller.grab_spectrum() for _ in range(max(Naverage, 1))) / max(Naverage, 1)
        self.dte_signal.emit(DataToExport(
            name=type(self).__name__,
            data=[DataFromPlugins(name='Spectrum', data=[spectrum], dim='Data1D', labels=['intensity'],
                                  units='counts', axes=[axis])]))

    def stop(self):
        pass


if __name__ == '__main__':
    main(__file__)
