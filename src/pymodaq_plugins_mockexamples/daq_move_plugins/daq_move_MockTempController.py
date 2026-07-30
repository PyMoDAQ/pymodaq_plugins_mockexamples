from pymodaq_utils.config import GlobalConfig

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType

from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataActuator

from pymodaq_plugins_mockexamples.hardware.temperature_controller import TempController
from pymodaq_plugins_mockexamples import Config

config = Config()


class DAQ_Move_MockTempController(DAQ_Move_base):
    """

    """
    _controller_units = 'K'
    is_multiaxes = True
    stage_names = ['Temperature']
    _epsilon = 0.01

    params = [
        {'title': 'PID Constants', 'name': 'constants', 'type': 'group', 'children': [
            {'title': 'Kp', 'name': 'kp', 'type': 'float',
             'value': config('temp_controller', 'kp')},
            {'title': 'Ki', 'name': 'ki', 'type': 'float', 'value': config('temp_controller', 'ki')},
            {'title': 'Kd', 'name': 'kd', 'type': 'float', 'value': config('temp_controller', 'kd')},
        ]},
         {'title': 'HasCooling:', 'name': 'has_cooling', 'type': 'led', 'value': TempController.has_cooling},
        {'title': 'Pause:', 'name': 'pause', 'type': 'led', 'value': False},
         {'title': 'Reset', 'name': 'reset', 'type': 'bool_push', 'value': False, 'label': 'Reset'},
             ] + comon_parameters_fun(is_multiaxes, stage_names, epsilon=_epsilon)
    data_actuator_type = DataActuatorType.DataActuator

    def ini_attributes(self):
        self.controller: TempController = None


    def get_actuator_value(self) -> DataActuator:
        """

        """
        pos = DataActuator(self._title, data=self.controller.temperature)
        pos = self.get_position_with_scaling(pos)
        return pos

    def commit_settings(self, param):
        if param.name() in ('kp', 'ki', 'kd'):
            setattr(self.controller, param.name(), param.value())
        elif param.name() == 'pause':
            self.controller.pause(param.value())
        elif param.name() == 'has_cooling':
            self.controller.has_cooling = param.value()

    def ini_stage(self, controller: TempController = None):
        """

        """
        if self.is_master:
            self.controller = TempController(
                kp=self.settings['constants', 'kp'],
                ki=self.settings['constants', 'ki'],
                kd=self.settings['constants', 'kd']
            )  # any object that will control the stages
        else:
            self.controller = controller

        info = "Temperature controller initialized"
        initialized = True

        return info, initialized

    def move_abs(self, position: DataActuator):
        """
            Make the absolute move from the given position after thread command signal was received in DAQ_Move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            DAQ_Move_base.set_position_with_scaling, DAQ_Move_base.poll_moving

        """
        position = self.check_bound(position)
        self.target_value = position
        self.controller.temperature = self.target_value.value(self.axis_unit)

    def move_rel(self, position: DataActuator):
        """

        """
        position = self.check_bound(self.current_value + position) - self.current_value
        self.target_value = position + self.current_value
        position = self.set_position_with_scaling(self.target_value)

        self.controller.temperature = self.target_value.value(self.axis_unit)

    def stop_motion(self):
        """
          Call the specific move_done function (depending on the hardware).

          See Also
          --------
          move_done
        """
        pass


if __name__ == '__main__':
    main(__file__)