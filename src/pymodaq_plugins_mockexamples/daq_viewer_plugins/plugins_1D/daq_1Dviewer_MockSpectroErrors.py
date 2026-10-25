import numpy as np

from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport

from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_1D.daq_1Dviewer_CookbookSpectrometer import \
    DAQ_1DViewer_CookbookSpectrometer


class DAQ_1DViewer_MockSpectroErrors(DAQ_1DViewer_CookbookSpectrometer):
    """
        Same as CookbookSpectrometer but the data is the average of the acquisitions and its error their standard
        deviation - testing errors saving/loading purpose
    """

    hardware_averaging = True

    def grab_data(self, Naverage=1, **kwargs):
        """Average Naverage spectra (at least 2, to have a standard deviation) and send their std as errors"""
        axis = Axis(data=self.controller.get_wavelength_axis(), label='wavelength', units='nm', index=0)
        spectra = self.average_spectra(max(Naverage, 2))
        self.dte_signal.emit(
            DataToExport(
                'Mock1D',
                data=[
                    DataFromPlugins(name='Mock1D',
                                    data=[spectra.mean(axis=0)],
                                    errors=[spectra.std(axis=0)],
                                    dim='Data1D',
                                    axes=[axis])]))


if __name__ == '__main__':
    main(__file__)
