"""Cookbook recipe 4b: 0D detector reading the positions of the axes of a controller driven by a vendor .NET assembly.

COPY this file for a detector of a controller that has several functions (here the encoders of three axes) behind one
object of the assembly. Alone it opens its own controller (master); with the same controller ID as the actuators
``CookbookDotNet`` it is a slave and shares their object: a controller must be opened once, not once per plugin.
ADAPT: ``params``, ``ini_detector``, and the acquisition in ``grab_data`` (name, labels and units of the data).
See ``daq_move_CookbookDotNet`` and ``hardware/dotnet_controller.py`` for what is specific to ``pythonnet``.
KEEP: the master/slave handling in ``ini_detector`` and ``close``, and the units given to the data.
"""
import numpy as np

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.dotnet_controller import MotionController, open_controller


class DAQ_0DViewer_CookbookDotNet(DAQ_Viewer_base):
    """Positions of the three axes of the simulated controller, read through ``MotionController``"""
    params = comon_parameters + [
        {'title': 'Port:', 'name': 'port', 'type': 'str', 'value': 'MOCK',
         'tip': 'Port of the controller, MOCK for the simulated assembly'},
        {'title': 'Assembly path:', 'name': 'assembly_path', 'type': 'browsepath', 'value': '', 'filetype': True,
         'tip': 'Full path to the .dll, empty to search it (environment variable MM_ASSEMBLY, name of the assembly)'},
    ]

    def ini_attributes(self):
        self.controller: MotionController = None

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = open_controller(self.settings['port'], self.settings['assembly_path'])
        else:  # a master actuator or detector shares its controller
            self.controller = controller
        info = self.controller.info()
        return f'{info.name}, firmware {info.firmware[0]}.{info.firmware[1]}', True

    def close(self):
        if self.is_master and self.controller is not None:
            self.controller.close()

    def grab_data(self, Naverage=1, **kwargs):
        positions = [np.array([self.controller.position(axis)]) for axis in range(self.controller.n_axes)]
        self.dte_signal.emit(DataToExport(
            name='CookbookDotNet',
            data=[DataFromPlugins(name='Positions', data=positions, dim='Data0D', labels=['X', 'Y', 'Z'],
                                  units='mm')]))

    def stop(self):
        pass

    def commit_settings(self, param):
        pass


if __name__ == '__main__':
    main(__file__)
