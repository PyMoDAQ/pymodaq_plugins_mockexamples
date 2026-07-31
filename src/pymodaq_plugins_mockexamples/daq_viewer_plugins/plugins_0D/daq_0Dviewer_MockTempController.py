import numpy as np


from pymodaq.utils.data import DataFromPlugins

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.temperature_controller import TempController



class DAQ_0DViewer_MockTempController(DAQ_Viewer_base):
    """ Get the temperature of the Temperature controller. Meant to be a slave of the MockTempController actuator
    """
    params = comon_parameters + []


    def ini_attributes(self):
        self.controller: TempController = None

    def commit_settings(self, param):
        """
        """
        pass


    def ini_detector(self, controller=None):
        """
        """
        if self.is_master:
            raise ValueError('This plugin can only be a Slave')
        else:
            self.controller = controller

        initialized = True
        info = 'Controller ok'
        return info, initialized

    def close(self):
        """
            not implemented.
        """
        pass

    def grab_data(self, Naverage=1, **kwargs):
        """


        """
        self.dte_signal.emit(DataToExport(self._title, data=[
            DataFromPlugins(name='Temperature',
                            data=[np.atleast_1d(self.controller.temperature),],
                            dim='Data0D', labels=['Temperature'],
                            units='K'),
            DataFromPlugins(name='Power',
                            data=[np.atleast_1d(self.controller.power)],
                            dim='Data0D', labels=['Power'],
                            units='W')
        ]))

    def stop(self):
        """
            not implemented.
        """
        return ""


if __name__ == '__main__':
    main(__file__)
