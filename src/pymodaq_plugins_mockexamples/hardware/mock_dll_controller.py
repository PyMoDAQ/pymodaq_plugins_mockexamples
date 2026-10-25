"""A simulated vendor library for a 3-axis motion controller: ``MockMotionLibrary`` behaves like a ``ctypes.CDLL``.

Most vendor drivers are written with ``ctypes`` on a DLL (or shared object) the manufacturer supplies. Without the
hardware, and so without the DLL, this module gives the driver (``dll_controller.py``) an object that is used exactly
like the loaded library: functions are looked up by name, the driver sets their ``argtypes`` and ``restype``, passes
handles, ``byref`` arguments, a structure and a callback created with ``CFUNCTYPE``, and gets integer error codes. So
the real ``ctypes`` code of the driver runs, and the tests cover it.

The C API that is simulated::

    int         mm_open(const char *port, void **handle);
    int         mm_close(void *handle);
    int         mm_get_info(void *handle, MM_Info *info);
    int         mm_move_abs(void *handle, int axis, double position);
    int         mm_get_position(void *handle, int axis, double *position);
    int         mm_is_moving(void *handle, int axis, int *moving);
    int         mm_stop(void *handle, int axis);
    int         mm_home(void *handle, int axis);
    int         mm_set_callback(void *handle, void (*callback)(int axis, int event));
    const char *mm_error_message(int code);

``MM_OK`` (0) is returned on success. The callback is called from a thread of the library when a move or a homing
ends or is stopped.
"""
import ctypes
import itertools
import threading
from time import monotonic
from typing import Callable, Optional

MM_OK = 0
MM_ERR_PORT = 1
MM_ERR_HANDLE = 2
MM_ERR_AXIS = 3
MM_ERR_RANGE = 4
ERROR_MESSAGES = {MM_OK: 'ok', MM_ERR_PORT: 'no controller on this port', MM_ERR_HANDLE: 'invalid handle',
                  MM_ERR_AXIS: 'invalid axis', MM_ERR_RANGE: 'position out of range'}

EVENT_MOVE_DONE = 1
EVENT_STOPPED = 2
EVENT_HOME_DONE = 3

N_AXES = 3
RANGE = (-50., 50.)  # mm
PORT = 'MOCK'

MM_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int)


class MM_Info(ctypes.Structure):
    """``typedef struct { char name[32]; int n_axes; int firmware[2]; } MM_Info;``"""
    _fields_ = [('name', ctypes.c_char * 32), ('n_axes', ctypes.c_int), ('firmware', ctypes.c_int * 2)]


class MockMotionController:
    """The simulated controller: three axes moving at constant speed, with a thread that reports the end of a move"""

    def __init__(self, speed: float = 25.):
        self.speed = speed  # mm/s
        self.callback: Optional[Callable[[int, int], None]] = None
        self._lock = threading.Lock()
        self._start = [0.] * N_AXES
        self._target = [0.] * N_AXES
        self._t0 = [0.] * N_AXES
        self._duration = [0.] * N_AXES
        self._timers: list[Optional[threading.Timer]] = [None] * N_AXES
        self._event = [EVENT_MOVE_DONE] * N_AXES

    def position(self, axis: int) -> float:
        with self._lock:
            return self._position(axis)

    def _position(self, axis: int) -> float:
        if self._duration[axis] == 0.:
            return self._target[axis]
        fraction = min(1., (monotonic() - self._t0[axis]) / self._duration[axis])
        return self._start[axis] + (self._target[axis] - self._start[axis]) * fraction

    def is_moving(self, axis: int) -> bool:
        with self._lock:
            return self._timers[axis] is not None

    def move_to(self, axis: int, target: float, end_event: int = EVENT_MOVE_DONE):
        with self._lock:
            self._cancel(axis)
            start = self._position(axis)
            self._start[axis], self._target[axis] = start, target
            self._t0[axis] = monotonic()
            self._duration[axis] = abs(target - start) / self.speed
            self._event[axis] = end_event
            timer = threading.Timer(self._duration[axis], self._arrived, args=(axis,))
            timer.daemon = True
            self._timers[axis] = timer
        timer.start()

    def stop(self, axis: int):
        with self._lock:
            moving = self._timers[axis] is not None
            self._cancel(axis)
            self._start[axis] = self._target[axis] = self._position(axis)
            self._duration[axis] = 0.
        if moving:
            self._notify(axis, EVENT_STOPPED)

    def _cancel(self, axis: int):
        if self._timers[axis] is not None:
            self._timers[axis].cancel()
            self._timers[axis] = None

    def _arrived(self, axis: int):
        """Runs in the thread of the timer, like the thread of a vendor library"""
        with self._lock:
            if self._timers[axis] is None:  # stopped or restarted in the meantime
                return
            self._timers[axis] = None
            self._duration[axis] = 0.
            event = self._event[axis]
        self._notify(axis, event)

    def _notify(self, axis: int, event: int):
        if self.callback is not None:
            self.callback(axis, event)

    def close(self):
        for axis in range(N_AXES):
            with self._lock:
                self._cancel(axis)
        self.callback = None


class _MockFunction:
    """A function of the library: carries the ``argtypes`` and ``restype`` the driver sets, as a ``ctypes`` one does

    Arguments are converted as ``ctypes`` would do: Python numbers and bytes are accepted for the simple types, and
    ``byref(x)`` gives access to the ``x`` object the function writes into.
    """

    def __init__(self, name: str, implementation: Callable):
        self.__name__ = name
        self._implementation = implementation
        self.argtypes: Optional[list] = None
        self.restype = ctypes.c_int

    def __call__(self, *args):
        if self.argtypes is not None:
            if len(args) != len(self.argtypes):
                raise TypeError(f'{self.__name__} takes {len(self.argtypes)} arguments ({len(args)} given)')
            args = tuple(self._convert(arg, argtype) for arg, argtype in zip(args, self.argtypes))
        result = self._implementation(*args)
        if self.restype is None:
            return None
        if self.restype is ctypes.c_char_p:
            return result
        return self.restype(result).value if isinstance(result, int) else result

    @staticmethod
    def _convert(arg, argtype):
        if hasattr(arg, '_obj'):  # a byref(...) object: the function writes in the wrapped ctypes object
            return arg._obj
        if isinstance(arg, ctypes._SimpleCData):
            return arg.value
        if isinstance(arg, argtype):  # a structure, a callback of the declared type, ...
            return arg
        converted = argtype.from_param(arg)  # what ctypes does: a TypeError for an argument of the wrong type
        return getattr(converted, 'value', arg)


class MockMotionLibrary:
    """Used instead of the loaded library: ``lib = MockMotionLibrary()``, then ``lib.mm_open(...)``

    Unknown names raise ``AttributeError`` like a library does when a symbol is missing.
    """

    def __init__(self, speed: float = 25.):
        self.speed = speed
        self._controllers: dict[int, MockMotionController] = {}
        self._handles = itertools.count(0x1000)
        self._functions = {name: _MockFunction(name, getattr(self, f'_{name}')) for name in (
            'mm_open', 'mm_close', 'mm_get_info', 'mm_move_abs', 'mm_get_position', 'mm_is_moving', 'mm_stop',
            'mm_home', 'mm_set_callback', 'mm_error_message')}
        self._functions['mm_error_message'].restype = ctypes.c_char_p

    def __getattr__(self, name: str) -> _MockFunction:
        if name.startswith('mm_') and name in self.__dict__.get('_functions', {}):
            return self._functions[name]
        raise AttributeError(f'undefined symbol: {name}')

    def _get(self, handle: int) -> Optional[MockMotionController]:
        return self._controllers.get(handle)

    def _mm_open(self, port: bytes, handle) -> int:
        if port != PORT.encode():
            return MM_ERR_PORT
        number = next(self._handles)
        self._controllers[number] = MockMotionController(self.speed)
        handle.value = number
        return MM_OK

    def _mm_close(self, handle: int) -> int:
        controller = self._controllers.pop(handle, None)
        if controller is None:
            return MM_ERR_HANDLE
        controller.close()
        return MM_OK

    def _mm_get_info(self, handle: int, info: MM_Info) -> int:
        if self._get(handle) is None:
            return MM_ERR_HANDLE
        info.name = b'MockMotion 3000'
        info.n_axes = N_AXES
        info.firmware[0], info.firmware[1] = 2, 7
        return MM_OK

    def _axis_call(self, handle: int, axis: int, call: Callable[[MockMotionController], None]) -> int:
        controller = self._get(handle)
        if controller is None:
            return MM_ERR_HANDLE
        if not 0 <= axis < N_AXES:
            return MM_ERR_AXIS
        call(controller)
        return MM_OK

    def _mm_move_abs(self, handle: int, axis: int, position: float) -> int:
        code = self._axis_call(handle, axis, lambda controller: None)  # validate the handle and the axis
        if code != MM_OK:
            return code
        if not RANGE[0] <= position <= RANGE[1]:
            return MM_ERR_RANGE
        return self._axis_call(handle, axis, lambda controller: controller.move_to(axis, position))

    def _mm_get_position(self, handle: int, axis: int, position) -> int:
        return self._axis_call(handle, axis, lambda controller: setattr(position, 'value', controller.position(axis)))

    def _mm_is_moving(self, handle: int, axis: int, moving) -> int:
        return self._axis_call(handle, axis,
                               lambda controller: setattr(moving, 'value', int(controller.is_moving(axis))))

    def _mm_stop(self, handle: int, axis: int) -> int:
        return self._axis_call(handle, axis, lambda controller: controller.stop(axis))

    def _mm_home(self, handle: int, axis: int) -> int:
        return self._axis_call(handle, axis, lambda controller: controller.move_to(axis, 0., EVENT_HOME_DONE))

    def _mm_set_callback(self, handle: int, callback) -> int:
        controller = self._get(handle)
        if controller is None:
            return MM_ERR_HANDLE
        controller.callback = callback  # a ctypes function pointer: calling it enters Python from this thread
        return MM_OK

    @staticmethod
    def _mm_error_message(code: int) -> bytes:
        return ERROR_MESSAGES.get(code, 'unknown error').encode()
