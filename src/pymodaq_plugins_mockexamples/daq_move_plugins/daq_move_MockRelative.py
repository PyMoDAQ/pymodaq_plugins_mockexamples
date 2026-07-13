from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun,
                                                          DataActuatorType, DataActuator, main)
from pymodaq.control_modules.daq_move_ui.utils import UiType

from pymodaq_plugins_mockexamples import config


class DAQ_Move_MockRelative(DAQ_Move_base):
    """ An actuator with no referencing and absolute values

    """
    _controller_units = ''

    is_multiaxes = True  # set to True if this plugin is controlled for a multiaxis controller (with a unique communication link)
    axes_names = ['']
    _epsilon = 0.01
    params = comon_parameters_fun(is_multiaxes, axes_names, epsilon=_epsilon)

    data_actuator_type = DataActuatorType.DataActuator
    ui_type = UiType.RELATIVE
    has_encoder = False

    def ini_attributes(self):
        self._internal_value = 0.

    def get_actuator_value(self) -> DataActuator:
        raise NotImplementedError

    def close(self):
        """
        Terminate the communication protocol
        """
        pass

    def commit_settings(self, param):
        pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        info = "Controller initialized"
        initialized = True
        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by position

        Parameters
        ----------
        value: (DataActuator) value of the absolute target positioning
        """

        raise NotImplementedError

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by position

        Parameters
        ----------
        value: (DataActuator) value of the relative target positioning
        """
        value = self.check_bound(self.current_value + value) - self.current_value
        self.target_value = value + self.current_value
        value = self.set_position_relative_with_scaling(value)
        self._internal_value += value.value(self.axis_unit)

    def move_home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """

        pass

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
