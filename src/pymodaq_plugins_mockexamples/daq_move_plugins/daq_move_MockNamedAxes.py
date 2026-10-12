
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, main, DataActuatorType, DataActuator  # base class
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun  # common set of parameters for all actuators

from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict
from ..hardware.multiaxis_wrapper import MultiAxis

from pymodaq_plugins_mockexamples import config


class DAQ_Move_MockNamedAxes(DAQ_Move_base):
    """
        Wrapper object to access the Mock fonctionnalities, similar wrapper for all controllers.

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = ''
    is_multiaxes = True
    _axis_names = dict(zip(['Xaxis', 'Yaxis', 'Zaxis'], MultiAxis.axes_indexes))
    _epsilons = 0.01

    params = comon_parameters_fun(axes_names=_axis_names, epsilon=_epsilons)
    data_actuator_type = DataActuatorType.DataActuator

    def ini_attributes(self):
        self.controller: MultiAxis = None

    def get_actuator_value(self) -> DataActuator:
        pos = DataActuator(self._title,
                           data=self.controller.get_value(self.axis_value),
                           units = self.axis_unit)
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        pass

    def commit_settings(self, param):
        pass

    def ini_stage(self, controller=None):
        """
            Initialize the controller and stages (axes) with given parameters.

            ============== ================================================ ==========================================================================================
            **Parameters**  **Type**                                         **Description**

            *controller*    instance of the specific controller object       If defined this hardware will use it and will not initialize its own controller instance
            ============== ================================================ ==========================================================================================

            Returns
            -------
            Easydict
                dictionnary containing keys:
                 * *info* : string displaying various info
                 * *controller*: instance of the controller object in order to control other axes without the need to init the same controller twice
                 * *stage*: instance of the stage (axis or whatever) object
                 * *initialized*: boolean indicating if initialization has been done corretly

            See Also
            --------
             daq_utils.ThreadCommand
        """
        if self.is_master:
            self.controller = MultiAxis()
        else:
            self.controller = controller
        info = "Mock MultiAxis"
        initialized = True
        return info, initialized

    def move_abs(self, position: DataActuator):
        position = self.check_bound(position)  #if user checked bounds, the defined bounds are applied here
        self.target_value = position
        position = self.set_position_with_scaling(position)
        pos = self.controller.set_value(self.axis_value, position.value(self.axis_unit))

    def move_rel(self, position: DataActuator):
        position = self.check_bound(self.current_value + position) - self.current_value
        self.target_value = position + self.current_value
        position = self.set_position_with_scaling(self.target_value)

        pos = self.controller.set_value(self.axis_value, position.value(self.axis_unit))

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
        self.move_done()


if __name__ == '__main__':
    main(__file__)
