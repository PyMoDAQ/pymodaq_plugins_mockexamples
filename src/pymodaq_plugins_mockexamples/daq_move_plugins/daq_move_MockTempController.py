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
    _controller_units = ['K', 'W']
    is_multiaxes = True
    stage_names = ['Temperature', 'Power']
    _epsilon = [0.01, 0.01]

    params = [
                 {'title': 'PID Constants', 'name': 'constants', 'type': 'group', 'children': [
                     {'title': 'Kp', 'name': 'kp', 'type': 'float',
                      'value': config('temp_controller', 'kp')},
                     {'title': 'Ki', 'name': 'ki', 'type': 'float', 'value': config('temp_controller', 'ki')},
                     {'title': 'Kd', 'name': 'kd', 'type': 'float', 'value': config('temp_controller', 'kd')},
                 ]},
                 {'title': 'HasCooling:', 'name': 'has_cooling', 'type': 'led', 'value': TempController.has_cooling},
                 {'title': 'Enabled:', 'name': 'enabled', 'type': 'led', 'value': False},
                 {'title': 'Reset', 'name': 'reset', 'type': 'bool_push', 'value': False, 'label': 'Reset'},
             ] + comon_parameters_fun(is_multiaxes, stage_names, epsilon=_epsilon)
    data_actuator_type = DataActuatorType.DataActuator

    def ini_attributes(self):
        self.controller: TempController = None


    def get_actuator_value(self) -> DataActuator:
        """

        """
        if self.axis_name == "Temperature":
            pos = DataActuator(self._title, data=self.controller.temperature, units=self.axis_unit)
        else:
            pos = DataActuator(self._title, data=self.controller.power.m_as(self.axis_unit), units=self.axis_unit)
        pos = self.get_position_with_scaling(pos)
        return pos

    def commit_settings(self, param):
        if param.name() in ('kp', 'ki', 'kd'):
            setattr(self.controller, param.name(), param.value())
        elif param.name() == 'enabled':
            self.controller.enable(param.value())
        elif param.name() == 'has_cooling':
            self.controller.has_cooling = param.value()
        elif param.name() == 'reset':
            self.controller.reset()

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

    def move_abs(self, value: DataActuator):
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
        value = self.check_bound(value)
        self.target_value = value
        if self.axis_name == "Temperature":
            self.controller.target_temperature = self.target_value.value(self.axis_unit)
        else:
            self.controller.power = self.target_value.value(self.axis_unit)
    def move_rel(self, value: DataActuator):
        """

        """
        value = self.check_bound(self.current_value + value) - self.current_value
        self.target_value = value + self.current_value
        value = self.set_position_with_scaling(self.target_value)
        if self.axis_name == "Temperature":
            self.controller.target_temperature = self.target_value.value(self.axis_unit)
        else:
            self.controller.power = self.target_value.value(self.axis_unit)

    def close(self) -> None:
        if self.is_master:
            self.controller.close()

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