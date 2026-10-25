"""Cookbook recipe 4a: multi-axis actuator on a vendor .NET assembly (``pythonnet``), with a move that ends by an event.

COPY this file for an actuator whose manufacturer supplies a .NET assembly (``Vendor.Device.dll``) for a controller
with several axes. It is the recipe of ``daq_move_CookbookDll`` with the driver of ``hardware/dotnet_controller.py``:
read that file for what is specific to ``pythonnet`` (``out`` parameters, events, exceptions, ``IDisposable``).
ADAPT: ``params`` (what the assembly needs to connect), ``_axis_names``, ``_controller_units``, the calls of the driver
in ``move_abs``, ``move_rel``, ``get_actuator_value``, ``move_home`` and ``stop_motion``.
KEEP:
- the master/slave handling in ``ini_stage`` and ``close``: the first axis (master) opens the controller, the others
  (slaves, same controller ID in the Dashboard) receive it;
- the event handling. The assembly raises the event from one of its own threads: ``_forward_event`` only emits a Qt
  signal, which is delivered to ``_on_motion_event`` in the thread of the plugin. Never call ``move_done`` or touch a
  widget from the thread of the assembly;
- ``user_condition_to_reach_target``: PyMoDAQ polls the position until it is within epsilon of the target, and also
  waits for the end-of-move event. The homing is not polled, so ``move_done`` is called when its event arrives.

Try it without the assembly: leave the port to ``MOCK``, the assembly is then the simulated one of
``hardware/mock_dotnet_controller.py``. The runtime of .NET and the loading of the assembly are in
``hardware/dotnet_runtime.py``.
"""
from qtpy.QtCore import Signal, Slot

from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, DataActuatorType,
                                                          DataActuator, main)

from pymodaq_plugins_mockexamples.hardware.dotnet_controller import MotionController, open_controller
from pymodaq_plugins_mockexamples.hardware.mock_dll_controller import (EVENT_MOVE_DONE, EVENT_STOPPED,
                                                                       EVENT_HOME_DONE)


class DAQ_Move_CookbookDotNet(DAQ_Move_base):
    """One axis of the simulated 3-axis controller, driven through ``MotionController`` on a .NET assembly"""
    _controller_units = 'mm'
    is_multiaxes = True
    _axis_names = {'X': 0, 'Y': 1, 'Z': 2}  # the assembly numbers its axes
    _epsilons = 0.01
    data_actuator_type = DataActuatorType.DataActuator
    params = comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilons) + [
        {'title': 'Port:', 'name': 'port', 'type': 'str', 'value': 'MOCK',
         'tip': 'Port of the controller, MOCK for the simulated assembly'},
        {'title': 'Assembly path:', 'name': 'assembly_path', 'type': 'browsepath', 'value': '', 'filetype': True,
         'tip': 'Full path to the .dll, empty to search it (environment variable MM_ASSEMBLY, name of the assembly)'},
    ]

    motion_event = Signal(int, int)  # axis, event: emitted from the thread of the assembly, received in this thread

    def ini_attributes(self):
        self.controller: MotionController = None
        self._move_finished = True
        self._homing = False
        self.motion_event.connect(self._on_motion_event)

    def ini_stage(self, controller=None):
        if self.is_master:
            self.controller = open_controller(self.settings['port'], self.settings['assembly_path'])
        else:  # a master axis shares its controller
            self.controller = controller
        self.controller.subscribe(self._forward_event)
        info = self.controller.info()
        return f'{info.name}, firmware {info.firmware[0]}.{info.firmware[1]}', True

    def close(self):
        if self.controller is not None:
            self.controller.unsubscribe(self._forward_event)
            if self.is_master:
                self.controller.close()

    def _forward_event(self, axis: int, event: int):
        """Called from the thread of the assembly: only emit the signal"""
        self.motion_event.emit(axis, event)

    @Slot(int, int)
    def _on_motion_event(self, axis: int, event: int):
        """Runs in the thread of the plugin"""
        if axis != self.axis_value:  # the controller is shared: events of the other axes come too
            return
        if event == EVENT_HOME_DONE and self._homing:
            self._homing = False
            self.move_done()
        elif event in (EVENT_MOVE_DONE, EVENT_STOPPED):
            self._move_finished = True

    def user_condition_to_reach_target(self) -> bool:
        return self._move_finished

    def get_actuator_value(self) -> DataActuator:
        position = DataActuator(data=self.controller.position(self.axis_value), units=self.axis_unit)
        return self.get_position_with_scaling(position)

    def move_abs(self, value: DataActuator):
        value = self.check_bound(value)
        self.target_value = value
        value = self.set_position_with_scaling(value)
        self._move_finished = False
        self.controller.move_abs(self.axis_value, value.value(self.axis_unit))

    def move_rel(self, value: DataActuator):
        value = self.check_bound(self.current_value + value) - self.current_value
        self.target_value = value + self.current_value
        value = self.set_position_with_scaling(self.target_value)
        self._move_finished = False
        self.controller.move_abs(self.axis_value, value.value(self.axis_unit))

    def move_home(self):
        self._homing = True
        self.controller.home(self.axis_value)

    def stop_motion(self):
        self.controller.stop(self.axis_value)

    def commit_settings(self, param):
        pass


if __name__ == '__main__':
    main(__file__)
