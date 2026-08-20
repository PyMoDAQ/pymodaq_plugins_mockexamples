from pymodaq.control_modules.move_utility_classes import main  # base class

from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_BSPiezoMirror import DAQ_Move_BSPiezoMirror


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