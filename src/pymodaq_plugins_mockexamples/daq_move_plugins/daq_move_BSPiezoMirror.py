import numpy as np

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, main, DataActuatorType  # base class
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun  # common set of parameters for all actuators
from pymodaq.utils.data import DataActuator
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread


from pymodaq_plugins_mockexamples.hardware.beam_steering import BeamSteering, BeamSteeringActuators



class DAQ_Move_BSPiezoMirror(DAQ_Move_base):
    """
    """

    _controller_units = ''
    is_multiaxes = True
    stage_names = BeamSteeringActuators.axes[:2]
    _epsilon = 1
    data_actuator_type = DataActuatorType.DataActuator

    params = [
            {'title': 'Tau (ms):', 'name': 'tau', 'type': 'int',
             'value': BeamSteering._tau * 1000, 'tip': 'Characteristic evolution time'},
             ] + comon_parameters_fun(is_multiaxes, stage_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: BeamSteering = None

    def get_actuator_value(self) -> DataActuator:
        pos = DataActuator(self._title,
                           data=[np.atleast_1d(self.controller.get_value(self.axis_name))],
                           units=self.axis_unit)
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        pass

    def commit_settings(self, param):
        if param.name() == 'tau':
            self.controller.tau = param.value() / 1000

    def ini_stage(self, controller=None):
        """

        """
        if self.is_master:
            self.controller = BeamSteering()
        else:
            self.controller = controller

        self.controller.tau = self.settings['tau'] / 1000

        info = ""
        initialized = True
        return info, initialized

    def move_abs(self, position):
        position = self.check_bound(position)  #if user checked bounds, the defined bounds are applied here
        self.target_value = position
        position = self.set_position_with_scaling(position)
        pos = self.controller.move_at(position.value(self.axis_unit), self.axis_name)

    def move_rel(self, position):
        position = self.check_bound(self.current_value + position) - self.current_value
        self.target_value = position + self.current_value
        position = self.set_position_with_scaling(self.target_value)
        pos = self.controller.move_at(position.value(self.axis_unit), self.axis_name)

    def move_home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """
        self.emit_status(ThreadCommand('Update_Status', ['Move Home not implemented']))

    def stop_motion(self):
        """
          Call the specific move_done function (depending on the hardware).

          See Also
          --------
          move_done
        """
        self.controller.stop(self.axis_name)
        self.move_done()


if __name__ == '__main__':
    main(__file__)