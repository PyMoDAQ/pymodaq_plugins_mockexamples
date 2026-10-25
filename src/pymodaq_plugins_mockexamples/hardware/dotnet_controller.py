"""Driver of the 3-axis motion controller of ``mock_dotnet_controller.py``, written like a driver for a vendor .NET
assembly with ``pythonnet``.

What differs from a ``ctypes`` driver (``dll_controller.py``): there is no ``argtypes`` or ``restype`` to declare,
``pythonnet`` converts the arguments and the results, but some conventions must be known:

- an ``out`` parameter of a .NET method is returned by ``pythonnet`` in a tuple, after the result of the method:
  ``ok, position = controller.TryGetPosition(axis)``;
- an event receives a Python function with ``+=`` (it is converted to a delegate) and gives it up with ``-=``. The
  function is stored in an attribute, to remove the very same object. The assembly raises the event from one of
  its threads: the function must only forward it to the listeners, which must not touch Qt widgets;
- a .NET exception is a Python exception of the .NET type: catch the exception type of the assembly (here
  ``MmException``) and read its ``Message`` (``str(exception)`` also holds the .NET stack trace);
- the objects that hold hardware are ``IDisposable``: call ``Dispose()`` when done (in ``close``);
- an enumeration value gives its number with ``int(...)``.

Load the real assembly with ``MotionController(load_assembly('Mm.Net', namespace='Mm'), port)`` (see
``dotnet_runtime.py``) or the simulated one with ``MotionController.mock()``.
"""
from typing import Callable

from pymodaq_plugins_mockexamples.hardware.dll_controller import ControllerInfo, MotionControllerError
from pymodaq_plugins_mockexamples.hardware.mock_dotnet_controller import MockMmNamespace
from pymodaq_plugins_mockexamples.hardware.mock_dll_controller import PORT, N_AXES


class MotionController:
    """Handle of an opened controller and its axes (numbered from 0), on a .NET assembly"""
    n_axes = N_AXES

    def __init__(self, api, port: str = PORT):
        """``api`` is the namespace of the assembly: ``import Mm`` with ``pythonnet``, or its simulation"""
        self._api = api
        self._controller = self._call(api.Controller.Open, port)
        self._listeners: list[Callable[[int, int], None]] = []
        self._handler = self._on_event  # kept in an attribute: ``-=`` must be given the object given to ``+=``
        self._controller.MoveFinished += self._handler

    @classmethod
    def mock(cls) -> 'MotionController':
        """The controller on the simulated assembly (no assembly or .NET runtime needed)"""
        return cls(MockMmNamespace())

    @property
    def _open(self):
        """The .NET controller, refused once closed"""
        if self._controller is None:
            raise MotionControllerError('The controller is closed')
        return self._controller

    def _call(self, method, *args):
        try:
            return method(*args)
        except self._api.MmException as exc:
            raise MotionControllerError(exc.Message) from None

    def _on_event(self, sender, args):
        """Called by the assembly, from one of its threads"""
        for listener in list(self._listeners):
            listener(args.Axis, int(args.Event))

    def subscribe(self, listener: Callable[[int, int], None]):
        """``listener(axis, event)`` is called, from a thread of the assembly, when a move ends (see the EVENT_*)"""
        self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[int, int], None]):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def info(self) -> ControllerInfo:
        info = self._call(lambda: self._open.Info)
        return ControllerInfo(info.Name, info.AxisCount, (info.FirmwareMajor, info.FirmwareMinor))

    def position(self, axis: int) -> float:
        ok, position = self._open.TryGetPosition(axis)  # the ``out`` parameter comes back in a tuple
        if not ok:
            raise MotionControllerError(f'Could not read the position of axis {axis}')
        return position

    def is_moving(self, axis: int) -> bool:
        return self._call(self._open.IsMoving, axis)

    def move_abs(self, axis: int, position: float):
        """Start the move; the assembly raises ``MoveFinished`` when it is over"""
        self._call(self._open.MoveAbs, axis, position)

    def stop(self, axis: int):
        self._call(self._open.Stop, axis)

    def home(self, axis: int):
        """Start the homing; the assembly raises ``MoveFinished`` when it is over"""
        self._call(self._open.Home, axis)

    def close(self):
        if self._controller is not None:
            self._controller.MoveFinished -= self._handler
            self._controller.Dispose()
            self._controller = None
        self._listeners.clear()


ASSEMBLY_NAMES = ['Mm.Net']  # name of the (imaginary) assembly, without .dll


def open_controller(port: str, assembly_path: str = '') -> MotionController:
    """The controller of the simulated assembly for the port ``MOCK``, else of the vendor assembly found by
    ``load_assembly`` (setting of the plugin, environment variable ``MM_ASSEMBLY``, name of the assembly)"""
    if port == PORT:
        return MotionController.mock()
    from pymodaq_plugins_mockexamples.hardware.dotnet_runtime import load_assembly
    return MotionController(load_assembly(ASSEMBLY_NAMES, path=assembly_path or None, env_var='MM_ASSEMBLY',
                                          namespace='Mm'), port)
