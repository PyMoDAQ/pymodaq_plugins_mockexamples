"""Ontology demo: the simulated spectrometer measuring the reference spectrum, see MockSpectroSample"""
from pymodaq.control_modules.viewer_utility_classes import main

from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_1D.daq_1Dviewer_MockSpectroSample import \
    DAQ_1DViewer_MockSpectroSample


class DAQ_1DViewer_MockSpectroReference(DAQ_1DViewer_MockSpectroSample):
    """Counts of the reference measurement, on a wavelength axis in nm"""
    kind = 'reference'


if __name__ == '__main__':
    main(__file__)
