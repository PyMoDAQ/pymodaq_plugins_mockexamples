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

The methods ``get_spectro_wl``, ``set_spectro_wl``, ``get_laser_wl``, ``set_laser_wl``, ``get_exposure_ms`` and
``set_exposure_ms`` are the interface that the spectrometer extension calls on a spectrometer plugin: copy them to be
driven by it (the laser ones only if the laser line can be set). Each one answers by a status command carrying the
value.

Try it with the actuator ``CookbookSpectrometer`` in the Dashboard (same controller ID), or alone: change the
central wavelength or the grating and the axis follows. See ``hardware/spectrometer.py`` for the simulated instrument.

Who runs where (GUI thread, plugin thread, driver thread): see the diagrams of "How an instrument plugin works with the
Dashboard" (``plugin_workflow``) in the developer guide of PyMoDAQ.
"""
import numpy as np
from qtpy import QtWidgets
from qtpy.QtCore import QThread

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
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
        {'title': 'Laser wavelength (nm):', 'name': 'laser_wl', 'type': 'list', 'value': 532.,
         'limits': [405., 515., 532., 632.8], 'tip': 'The laser line is the line that the spectrometer measures'},
        {'title': 'Exposure (ms):', 'name': 'exposure_ms', 'type': 'int', 'value': 100, 'min': 1,
         'tip': 'The signal is proportional to the exposure time (100 ms gives the reference signal)'},
    ]

    def ini_attributes(self):
        self.controller: Spectrometer = None

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = Spectrometer()
            self.controller.grating = self.settings['grating']  # apply the settings loaded from a preset
            self.controller.set_wavelength(self.settings['central_wavelength'])
            self.controller.peak_wavelength = self.settings['laser_wl']
            self.controller.exposure_ms = self.settings['exposure_ms']
        else:  # a master actuator shares its instrument: do not move its grating
            self.controller = controller
            self.settings.child('grating').setValue(self.controller.grating)
            self.settings.child('central_wavelength').setValue(self.controller.get_wavelength())
            self.settings.child('laser_wl').setValue(self.controller.peak_wavelength)
            self.settings.child('exposure_ms').setValue(self.controller.exposure_ms)
        return self.controller.infos, True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.close()

    def commit_settings(self, param):
        if param.name() == 'grating':
            self.controller.grating = param.value()
        elif param.name() == 'central_wavelength':
            self.controller.set_wavelength(param.value())
        elif param.name() == 'laser_wl':
            self.controller.peak_wavelength = param.value()
        elif param.name() == 'exposure_ms':
            self.controller.exposure_ms = param.value()

    def get_spectro_wl(self):
        """Interface of the spectrometer extension: emit the central wavelength (the "grating" position)"""
        self.emit_status(ThreadCommand('spectro_wl', [self.settings['central_wavelength']]))

    def set_spectro_wl(self, spectro_wl: float):
        """Interface of the spectrometer extension: set the central wavelength and emit the new one"""
        self.controller.set_wavelength(spectro_wl)
        self.settings.child('central_wavelength').setValue(spectro_wl)
        QtWidgets.QApplication.processEvents()
        self.get_spectro_wl()

    def get_laser_wl(self):
        """Interface of the spectrometer extension: emit the wavelength of the laser"""
        self.emit_status(ThreadCommand('laser_wl', [self.settings['laser_wl']]))

    def set_laser_wl(self, laser_wl: float):
        """Interface of the spectrometer extension: set the wavelength of the laser and emit the new one"""
        self.controller.peak_wavelength = laser_wl
        self.settings.child('laser_wl').setValue(laser_wl)
        QtWidgets.QApplication.processEvents()
        self.get_laser_wl()

    def get_exposure_ms(self):
        """Interface of the spectrometer extension: emit the exposure time"""
        self.emit_status(ThreadCommand('exposure_ms', [self.settings['exposure_ms']]))

    def set_exposure_ms(self, exposure: int):
        """Interface of the spectrometer extension: set the exposure time and emit the new one"""
        self.controller.exposure_ms = exposure
        self.settings.child('exposure_ms').setValue(exposure)
        QtWidgets.QApplication.processEvents()
        self.get_exposure_ms()

    def grab_data(self, Naverage=1, **kwargs):
        axis = Axis(data=self.controller.get_wavelength_axis(), label='wavelength', units='nm', index=0)
        spectrum = self.average_spectra(Naverage).mean(axis=0)
        self.dte_signal.emit(DataToExport(
            name='CookbookSpectrometer',
            data=[DataFromPlugins(name='Spectrum', data=[spectrum], dim='Data1D', labels=['intensity'],
                                  axes=[axis])]))

    def average_spectra(self, Naverage: int) -> np.ndarray:
        """Naverage spectra, each one taking the exposure time"""
        spectra = []
        for _ in range(max(Naverage, 1)):
            QThread.msleep(self.settings['exposure_ms'])
            spectra.append(self.controller.grab_spectrum())
        return np.array(spectra)

    def stop(self):
        self.controller.stop()


if __name__ == '__main__':
    main(__file__)
