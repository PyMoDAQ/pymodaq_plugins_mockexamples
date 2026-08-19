from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_BSPiezoMirror import DAQ_Move_BSPiezoMirror

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, main  # base class
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun  # common set of parameters for all actuators

from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict
from pymodaq_plugins_mockexamples.hardware.beam_steering import BeamSteering, BeamSteeringActuators

from pymodaq_plugins_mockexamples import config


class DAQ_Move_BSPiezoMirrorRunTimeError(DAQ_Move_BSPiezoMirror):
    """
    """

    def get_actuator_value(self):
        raise RuntimeError('Testing Purpose')
        axis = self.settings['multiaxes', 'axis']
        pos = self.controller.get_value(axis)
        pos = self.get_position_with_scaling(pos)
        return pos


if __name__ == '__main__':
    main(__file__)