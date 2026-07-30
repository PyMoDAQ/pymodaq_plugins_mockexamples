import numpy as np


from pymodaq.utils.data import DataFromPlugins

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.heater import HeaterController



class DAQ_0DViewer_MockHeater(DAQ_Viewer_base):
    """
    """
    params = comon_parameters + [
        {'title:': 'Noise', 'name': 'noise', 'type': 'float', 'value': HeaterController._noise},
        {'title:': 'Ambiant temp', 'name': 'ambiant_temp', 'type': 'float',
         'value': HeaterController._ambiant_temperature}
              ]


    def ini_attributes(self):
        self.controller: HeaterController = None
        self.ind_data = 0

    def commit_settings(self, param):
        """
        """
        if param.name() == 'noise':
            self.controller.noise = param.value()
        elif param.name() == 'ambiant_temp':
            self.controller.ambiant_temp = param.value()


    def ini_detector(self, controller=None):
        """
        """
        if self.is_master:
            self.controller = HeaterController()
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
        temperature = self.controller.grab()
        self.dte_signal.emit(DataToExport(self._title, data=[
            DataFromPlugins(name=self._title, data=[np.array([temperature])],
                            dim='Data0D', labels=['Temperature'])]))

    def stop(self):
        """
            not implemented.
        """
        return ""


if __name__ == '__main__':
    main(__file__)
