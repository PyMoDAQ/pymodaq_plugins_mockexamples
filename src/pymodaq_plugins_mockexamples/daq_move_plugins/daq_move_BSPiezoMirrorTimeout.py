from qtpy import QtCore

from pymodaq.control_modules.move_utility_classes import main  # base class

from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_BSPiezoMirror import (
    DAQ_Move_BSPiezoMirror, BeamSteering)
from pymodaq_utils.config import GlobalConfig as Config


config = Config()



class DAQ_Move_BSPiezoMirrorTimeout(DAQ_Move_BSPiezoMirror):
    """
    """

    def ini_stage(self, controller=None):
        """

        """
        self.ini_stage_init(controller, BeamSteering())
        self.controller.tau = self.settings['tau'] / 1000
        QtCore.QThread.msleep(2 * config('pymodaq', 'control_modules', 'control_module_ini_polling') * 1000)  # simulating a very long initialization

        raise IOError('Hardware Timeout: Testing Purpose')  # simulating an error in initialization !!!
        info = ""
        initialized = True
        return info, initialized


if __name__ == '__main__':
    main(__file__)