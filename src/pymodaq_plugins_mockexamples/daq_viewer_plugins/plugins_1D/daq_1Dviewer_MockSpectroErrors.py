import numpy as np

from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport

from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_1D.daq_1Dviewer_CookbookSpectrometer import \
    DAQ_1DViewer_CookbookSpectrometer


class DAQ_1DViewer_MockSpectroErrors(DAQ_1DViewer_CookbookSpectrometer):
    """
        Same as CookbookSpectrometer but the instrument averages the acquisitions itself (``hardware_averaging``)
        and the plugin fills the ``errors`` of the data, as PyMoDAQ does when it averages: the standard error of the
        mean, sigma / sqrt(N), with sigma the standard deviation of the N acquisitions (ddof=1).
        Testing errors saving/loading purpose
    """

    hardware_averaging = True

    def grab_data(self, Naverage=1, **kwargs):
        """Average Naverage spectra (at least 2, to have a standard deviation) and send the standard error"""
        axis = Axis(data=self.controller.get_wavelength_axis(), label='wavelength', units='nm', index=0)
        spectra = self.average_spectra(max(Naverage, 2))
        n_spectra = len(spectra)
        dwa = DataFromPlugins(name='Mock1D',
                              data=[spectra.mean(axis=0)],
                              errors=[spectra.std(axis=0, ddof=1) / np.sqrt(n_spectra)],
                              dim='Data1D',
                              axes=[axis])
        dwa.n_averaged = n_spectra
        self.dte_signal.emit(DataToExport('Mock1D', data=[dwa]))


if __name__ == '__main__':
    main(__file__)
