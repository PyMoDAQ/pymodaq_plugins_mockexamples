"""Cookbook recipe 3a: 1D detector with an axis that is calibrated and changes: a spectrometer.

COPY this file for an instrument whose data axis is not fixed: a spectrometer (the wavelength of each pixel depends
on the central wavelength and on the grating), an oscilloscope (time base), an analyser...
ADAPT: ``params``, ``ini_detector`` and ``grab_data`` (what the driver gives for the data and for the axis).
KEEP:
- the axis is asked to the instrument at every grab and sent with the data. Another module (here the actuator
  ``CookbookSpectrometer``, a slave that turns the grating) can change it at any time;
- the units of the axis and of the data;
- the master/slave handling in ``ini_detector`` and ``close``: alone the detector owns the instrument, with the
  same controller ID as the actuator it shares the instrument of the master.

Try it with the actuator ``CookbookSpectrometer`` in the Dashboard (same controller ID), or alone: change the
central wavelength or the grating and the axis follows. See ``hardware/spectrometer.py`` for the simulated instrument.
"""
import numpy as np

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins, Axis
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.spectrometer import Spectrometer


class DAQ_1DViewer_CookbookSpectrometer(DAQ_Viewer_base):
    """Spectrum of the simulated spectrometer, on a wavelength axis in nm"""
    params = comon_parameters + [
        {'title': 'Grating:', 'name': 'grating', 'type': 'list', 'value': next(iter(Spectrometer.gratings)),
         'limits': list(Spectrometer.gratings), 'tip': 'The dispersion of the grating sets the range of the axis'},
        {'title': 'Central wavelength (nm):', 'name': 'central_wavelength', 'type': 'float', 'value': 532.,
         'min': 0, 'tip': 'Turns the grating. An actuator that shares the instrument can turn it too'},
    ]

    def ini_attributes(self):
        self.controller: Spectrometer = None

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = Spectrometer()
            self.controller.grating = self.settings['grating']  # apply the settings loaded from a preset
            self.controller.set_wavelength(self.settings['central_wavelength'])
        else:  # a master actuator shares its instrument: do not move its grating
            self.controller = controller
            self.settings.child('grating').setValue(self.controller.grating)
            self.settings.child('central_wavelength').setValue(self.controller.get_wavelength())
        return self.controller.infos, True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.close()

    def commit_settings(self, param):
        if param.name() == 'grating':
            self.controller.grating = param.value()
        elif param.name() == 'central_wavelength':
            self.controller.set_wavelength(param.value())

    def grab_data(self, Naverage=1, **kwargs):
        axis = Axis(data=self.controller.get_wavelength_axis(), label='wavelength', units='nm', index=0)
        spectrum = np.mean([self.controller.grab_spectrum() for _ in range(Naverage)], axis=0)
        self.dte_signal.emit(DataToExport(
            name='CookbookSpectrometer',
            data=[DataFromPlugins(name='Spectrum', data=[spectrum], dim='Data1D', labels=['intensity'],
                                  axes=[axis])]))

    def stop(self):
        self.controller.stop()


if __name__ == '__main__':
    main(__file__)
