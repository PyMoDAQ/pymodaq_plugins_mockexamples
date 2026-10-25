"""A simulated vendor .NET assembly for a 3-axis motion controller: ``MockMmNamespace`` is used like the namespace ``Mm``
that ``pythonnet`` gives once the assembly is referenced.

The driver (``dotnet_controller.py``) only uses what ``pythonnet`` gives: the classes of the namespace, their static
methods, properties, an ``out`` parameter (returned in a tuple by ``pythonnet``), an event that receives a Python
function with ``+=``, an exception type to catch, ``IDisposable``. This module offers the same, so the code of the
driver runs and is tested without the assembly. It is the same device as ``mock_dll_controller.py``.

The C# API that is simulated::

    namespace Mm {
        public class MmException : Exception { }
        public enum MoveEvent { MoveDone = 1, Stopped = 2, HomeDone = 3 }
        public class MoveEventArgs : EventArgs { public int Axis; public MoveEvent Event; }
        public class ControllerInfo { public string Name; public int AxisCount; public int FirmwareMajor, FirmwareMinor; }
        public class Controller : IDisposable {
            public static Controller Open(string port);
            public ControllerInfo Info { get; }
            public void MoveAbs(int axis, double position);
            public bool TryGetPosition(int axis, out double position);
            public bool IsMoving(int axis);
            public void Stop(int axis);
            public void Home(int axis);
            public event EventHandler<MoveEventArgs> MoveFinished;   // raised from a thread of the assembly
            public void Dispose();
        }
    }
"""
import enum
from typing import Callable, Optional

from pymodaq_plugins_mockexamples.hardware.mock_dll_controller import (MockMotionController, N_AXES, RANGE, PORT,
                                                                       EVENT_MOVE_DONE, EVENT_STOPPED,
                                                                       EVENT_HOME_DONE)


class MmException(Exception):
    """A .NET exception: the text is in ``Message``"""

    @property
    def Message(self) -> str:
        return str(self.args[0])


class MoveEvent(enum.IntEnum):
    MoveDone = EVENT_MOVE_DONE
    Stopped = EVENT_STOPPED
    HomeDone = EVENT_HOME_DONE


class MoveEventArgs:
    def __init__(self, axis: int, event: MoveEvent):
        self.Axis = axis
        self.Event = event


class ControllerInfo:
    Name = 'MockMotion .NET'
    AxisCount = N_AXES
    FirmwareMajor = 3
    FirmwareMinor = 1


class _Event:
    """A .NET event: ``controller.MoveFinished += handler`` adds a listener, ``-=`` removes it"""

    def __init__(self):
        self._handlers: list[Callable] = []

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        if handler in self._handlers:
            self._handlers.remove(handler)
        return self

    def invoke(self, sender, args):
        for handler in list(self._handlers):
            handler(sender, args)


class Controller:
    """The simulated ``Mm.Controller``"""
    speed = 25.  # mm/s

    def __init__(self, port: str):
        self._engine: Optional[MockMotionController] = MockMotionController(self.speed)
        self._engine.callback = self._raise_event
        self._move_finished = _Event()

    @staticmethod
    def Open(port: str) -> 'Controller':
        if port != PORT:
            raise MmException(f'No controller on port {port}')
        return Controller(port)

    @property
    def MoveFinished(self) -> _Event:
        return self._move_finished

    @MoveFinished.setter
    def MoveFinished(self, event: _Event):
        pass  # what ``controller.MoveFinished += handler`` assigns back: the same event

    @property
    def Info(self) -> ControllerInfo:
        self._check_axis(0)
        return ControllerInfo()

    def _check_axis(self, axis: int):
        if self._engine is None:
            raise MmException('The controller is disposed')
        if not 0 <= axis < N_AXES:
            raise MmException(f'Invalid axis {axis}')

    def _raise_event(self, axis: int, event: int):
        """Called by the simulation from its own thread, like the thread of a vendor assembly"""
        self._move_finished.invoke(self, MoveEventArgs(axis, MoveEvent(event)))

    def MoveAbs(self, axis: int, position: float):
        self._check_axis(axis)
        if not RANGE[0] <= position <= RANGE[1]:
            raise MmException('Position out of range')
        self._engine.move_to(axis, float(position))

    def TryGetPosition(self, axis: int):
        """``out double position``: ``pythonnet`` returns the result and the ``out`` values in a tuple"""
        if self._engine is None or not 0 <= axis < N_AXES:
            return False, 0.
        return True, self._engine.position(axis)

    def IsMoving(self, axis: int) -> bool:
        self._check_axis(axis)
        return self._engine.is_moving(axis)

    def Stop(self, axis: int):
        self._check_axis(axis)
        self._engine.stop(axis)

    def Home(self, axis: int):
        self._check_axis(axis)
        self._engine.move_to(axis, 0., EVENT_HOME_DONE)

    def Dispose(self):
        if self._engine is not None:
            self._engine.close()
            self._engine = None


class MockMmNamespace:
    """Used instead of ``import Mm``: ``api = MockMmNamespace()``, then ``api.Controller.Open(...)``"""
    Controller = Controller
    MmException = MmException
    MoveEvent = MoveEvent
