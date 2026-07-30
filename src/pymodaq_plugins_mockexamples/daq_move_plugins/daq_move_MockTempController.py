from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType

from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataActuator

from pymodaq_plugins_mockexamples.hardware.heater import HeaterController


class DAQ_Move_MockTempController(DAQ_Move_base):
    """
        Wrapper object to access the Mock fonctionnalities, similar wrapper for all controllers.

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = 'W'
    is_multiaxes = True
    stage_names = ['Heater']
    _epsilon = 0.01

    params = [] + comon_parameters_fun(is_multiaxes, stage_names, epsilon=_epsilon)
    data_actuator_type = DataActuatorType.DataActuator

    def ini_attributes(self):
        self.controller: HeaterController = None


    def get_actuator_value(self) -> DataActuator:
        """

        """
        pos = DataActuator(self._title, data=self.controller.check_position())
        pos = self.get_position_with_scaling(pos)
        return pos

    def commit_settings(self, param):
        pass

    def ini_stage(self, controller: HeaterController = None):
        """

        """
        if self.is_master:
            self.controller = HeaterController()  # any object that will control the stages
        else:
            self.controller = controller

        info = "Boiler controller initialized"
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
        self.controller.move_abs(self.target_value.value(self.axis_unit))

    def move_rel(self, position: DataActuator):
        """

        """
        position = self.check_bound(self.current_value + position) - self.current_value
        self.target_value = position + self.current_value
        position = self.set_position_with_scaling(self.target_value)

        self.controller.move_rel(position.value(self.axis_unit))

    def stop_motion(self):
        """
          Call the specific move_done function (depending on the hardware).

          See Also
          --------
          move_done
        """
        self.move_done()

if __name__ == '__main__':
    main(__file__)