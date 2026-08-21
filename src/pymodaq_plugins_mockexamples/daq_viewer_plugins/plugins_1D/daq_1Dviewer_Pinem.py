import numpy as np
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_mockexamples.hardware.pinem_simulator import PinemGenerator


class DAQ_1DViewer_Pinem(DAQ_Viewer_base):
    """ Instrument plugin class for a 1D viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

    """
    params = comon_parameters + [
        {'title': 'g', 'name': 'g', 'type': 'slide', 'value': 1, 'default': 1, 'min': 0,
         'max': 5, 'subtype': 'linear'},
        # the strength of the Signal to noise ratio is solely dependent on the amplitude of the signal
        {'title': 'amp', 'name': 'amplitude', 'type': 'slide', 'value': 20, 'default': 20, 'min': 5,
         'max': 500, 'subtype': 'linear'},
        {'title': 'omg', 'name': 'omega', 'type': 'slide', 'value': 1.5, 'default': 1.5, 'min': 0.1,
         'max': 4.5, 'subtype': 'linear'},
        {'title': 'offset', 'name': 'offset', 'type': 'slide', 'value': 0.5, 'default': 0.5,
         'min': 0.0,
         'max': 5.0, 'subtype': 'linear'},
        {'title': 'noise', 'name': 'noise', 'type': 'bool', 'value': False, 'default': False},
        {'title': 'background', 'name': 'background', 'type': 'slide', 'value': 0.1, 'default': 0.1,
         'min': 0.0,
         'max': 1.0, 'subtype': 'linear'},
        {'title': 'remove_background', 'name': 'remove_background', 'type': 'bool', 'value': True,
         'default': True}
        # elements to be added here as dicts in order to control your custom stage
        ############
    ]

    def ini_attributes(self):
        self.controller: PinemGenerator = None
        self.x_axis = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "g":
            self.controller.g = param.value()

        elif param.name() == 'amplitude':
            self.controller.amplitude = param.value()

        elif param.name() == 'offset':
            self.controller.offset = param.value()

        elif param.name() == 'noise':
            self.controller.noise = param.value()

        elif param.name() == 'background':
            self.controller.background = param.value()

        elif param.name() == 'remove_background':
            self.controller.remove_background = param.value()

        elif param.name() == 'omega':
            self.controller.omg = param.value()

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        if self.is_master:
            self.controller = PinemGenerator(1024, 0.05, 'Gaussian',
                                             amplitude=self.settings['amplitude'])
        else:
            self.controller = comon_parameters

        info = "Whatever info you want to log"
        initialized = True
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        ...

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        data_array = self.controller.gen_data()
        axis = Axis('energy', data=self.controller.x)
        self.dte_signal.emit(DataToExport('Pinem',
                                          data=[DataFromPlugins(name='Spectrum', data=[data_array],
                                                                dim='Data1D', labels=['Spectrum'],
                                                                axes=[axis]),
                                                ]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__)
