import numpy as np


from pymodaq.utils.data import DataFromPlugins

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq_data import DataToExport

from pymodaq_plugins_mockexamples.hardware.boiler import BoilerController



class DAQ_0DViewer_Boiler(DAQ_Viewer_base):
    """
    """
    params = comon_parameters + [
        {'title:': 'Noise', 'name': 'noise', 'type': 'float', 'value': BoilerController._noise},
        {'title:': 'Ambiant temp', 'name': 'ambiant_temp', 'type': 'float',
         'value': BoilerController._ambiant_temperature}
              ]


    def ini_attributes(self):
        self.controller: BoilerController = None
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
            self.controller = BoilerController()
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
        self.dte_signal.emit(DataToExport('Boiler', data=[
            DataFromPlugins(name='Boiler', data=[np.array([temperature])],
                            dim='Data0D', labels=['Temperature'])]))

    def stop(self):
        """
            not implemented.
        """
        return ""


if __name__ == '__main__':
    main(__file__)
