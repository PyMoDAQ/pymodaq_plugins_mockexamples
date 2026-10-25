"""Cookbook recipe 1b: 0D detector reading a voltage through a serial port, with a driver written directly on it.

COPY this file for a detector read through the same kind of link. Alone it creates its own controller (master); with
the same controller ID as the actuator ``CookbookSerial`` it is a slave and shares the driver of the actuator, which is how a
device with several functions (here a stage and a voltmeter) is split in several plugins.
ADAPT: ``params``, ``ini_detector``, and the acquisition in ``grab_data`` (name, labels and units of the data).
KEEP: the master/slave handling in ``ini_detector`` and ``close``, and the units given to the data.
"""
import numpy as np

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.mock_instrument import MockSerialPort
from pymodaq_plugins_mockexamples.hardware.serial_stage import SerialStage


class DAQ_0DViewer_CookbookSerial(DAQ_Viewer_base):
    """Voltmeter of the simulated device, read through ``SerialStage``"""
    params = comon_parameters + [
        {'title': 'Serial port:', 'name': 'port', 'type': 'str', 'value': 'MOCK',
         'tip': 'Name of the serial port (COM3, /dev/ttyUSB0), MOCK for the simulated device'},
        {'title': 'Baudrate:', 'name': 'baudrate', 'type': 'int', 'value': 9600},
    ]

    def ini_attributes(self):
        self.controller: SerialStage = None

    def ini_detector(self, controller=None):
        if self.is_master:
            port = MockSerialPort() if self.settings['port'] == 'MOCK' else self.settings['port']
            self.controller = SerialStage(port, baudrate=self.settings['baudrate'])
        else:  # a master actuator or detector shares its controller
            self.controller = controller
        return self.controller.identity(), True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.close()

    def grab_data(self, Naverage=1, **kwargs):
        voltage = np.mean([self.controller.read_voltage() for _ in range(Naverage)])
        self.dte_signal.emit(DataToExport(
            name='CookbookSerial',
            data=[DataFromPlugins(name='Voltage', data=[np.array([voltage])], dim='Data0D', labels=['voltage'],
                                  units='V')]))

    def stop(self):
        pass

    def commit_settings(self, param):
        pass


if __name__ == '__main__':
    main(__file__)
