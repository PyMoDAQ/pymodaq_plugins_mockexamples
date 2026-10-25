"""Cookbook recipe 2b: 0D detector reading a voltage through VISA, with a driver written directly on pyvisa.

COPY this file for a detector read through the same kind of link. Alone it creates its own controller (master); with
the same controller ID as the actuator ``CookbookVisa`` it is a slave and shares the driver of the actuator, which is how a
device with several functions (here a stage and a voltmeter) is split in several plugins.
ADAPT: ``params``, ``ini_detector``, and the acquisition in ``grab_data`` (name, labels and units of the data).
KEEP: the master/slave handling in ``ini_detector`` and ``close``, and the units given to the data.
"""
import numpy as np

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.mock_instrument import MockVisaResource
from pymodaq_plugins_mockexamples.hardware.visa_meter import VisaMeter


class DAQ_0DViewer_CookbookVisa(DAQ_Viewer_base):
    """Voltmeter of the simulated device, read through ``VisaMeter``"""
    params = comon_parameters + [
        {'title': 'VISA address:', 'name': 'address', 'type': 'str', 'value': 'MOCK',
         'tip': 'VISA resource, for instance TCPIP0::192.168.0.5::INSTR, MOCK for the simulated device'},
        {'title': 'Timeout (ms):', 'name': 'visa_timeout', 'type': 'int', 'value': 2000},
    ]

    def ini_attributes(self):
        self.controller: VisaMeter = None

    def ini_detector(self, controller=None):
        if self.is_master:
            address = self.settings['address']
            self.controller = VisaMeter(MockVisaResource() if address == 'MOCK' else address,
                                        timeout=self.settings['visa_timeout'])
        else:  # a master actuator or detector shares its controller
            self.controller = controller
        return self.controller.identity(), True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.close()

    def grab_data(self, Naverage=1, **kwargs):
        voltage = np.mean([self.controller.read_voltage() for _ in range(Naverage)])
        self.dte_signal.emit(DataToExport(
            name='CookbookVisa',
            data=[DataFromPlugins(name='Voltage', data=[np.array([voltage])], dim='Data0D', labels=['voltage'],
                                  units='V')]))

    def stop(self):
        pass

    def commit_settings(self, param):
        pass


if __name__ == '__main__':
    main(__file__)
