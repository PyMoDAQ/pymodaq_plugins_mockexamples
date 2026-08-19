from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_BSPiezoMirror import DAQ_Move_BSPiezoMirror

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, main  # base class
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun  # common set of parameters for all actuators

from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict
from pymodaq_plugins_mockexamples.hardware.beam_steering import BeamSteering, BeamSteeringActuators

from pymodaq_plugins_mockexamples import config


class DAQ_Move_BSPiezoMirrorUninitializing(DAQ_Move_BSPiezoMirror):
    """
    """

    def ini_stage(self, controller=None):
        """

        """
        self.ini_stage_init(controller, BeamSteering())
        self.controller.tau = self.settings['tau'] / 1000
        raise IOError('Testing Purpose')  # simulating an error in initialization !!!
        info = ""
        initialized = True
        return info, initialized


if __name__ == '__main__':
    main(__file__)