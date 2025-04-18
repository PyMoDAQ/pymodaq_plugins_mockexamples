from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun,
                                                          DataActuatorType, DataActuator, main)


from pymodaq_plugins_mockexamples import config


class DAQ_Move_MockBinary(DAQ_Move_base):
    """ A very simple actuator plugin setting/getting the value one has set into it

    The value could only be 0 or 1

    """
    _controller_units = ''

    is_multiaxes = True  # set to True if this plugin is controlled for a multiaxis controller (with a unique communication link)
    axes_names = ['']
    _epsilon = 0.01
    params = comon_parameters_fun(is_multiaxes, axes_names, epsilon=_epsilon)
    data_actuator_type = DataActuatorType.DataActuator

    def ini_attributes(self):
        self._internal_state = 0

    @property
    def internal_state(self):
        return self._internal_state

    @internal_state.setter
    def internal_state(self, value: int):
        if int(value) == 0 or int(value) == 1:
            self._internal_state = int(value)

    def get_actuator_value(self):
        pos = DataActuator(data=self.internal_state)
        pos = self.get_position_with_scaling(pos)
        return pos

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

    def move_abs(self, position: DataActuator):
        """ Move the actuator to the absolute target defined by position

        Parameters
        ----------
        position: (float) value of the absolute target positioning
        """

        position = self.check_bound(position)  #if user checked bounds, the defined bounds are applied here
        self.target_value = position
        position = self.set_position_with_scaling(position)  # apply scaling if the user specified one

        self.internal_state = position.value()

    def move_rel(self, position):
        """ Move the actuator to the relative target actuator value defined by position

        Parameters
        ----------
        position: (flaot) value of the relative target positioning
        """
        pass

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
