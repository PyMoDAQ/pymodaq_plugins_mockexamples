"""Driver of the 3-axis motion controller of ``mock_dll_controller.py``, written like a driver for a vendor DLL.

This is the ``ctypes`` layer that a plugin author writes (or finds written) on a manufacturer library:

- ``_declare`` gives every function its ``argtypes`` and ``restype``: without them ``ctypes`` guesses (C ``int``
  arguments and result) and a 64 bits pointer or a ``double`` is silently corrupted;
- the library hands out an opaque *handle* (``void *``) received through ``byref`` and given back to every call;
- every function returns an integer error code, turned into an exception by ``_check`` with the message of the library;
- the library fills a structure (``MM_Info``);
- a callback made with ``CFUNCTYPE`` is registered once and kept in an attribute: if Python collects it while the
  library still holds the pointer, the next call crashes the interpreter. It is called from a thread of the library,
  so it only forwards the event to the listeners, which must not touch Qt widgets.

Load the real library with ``MotionController.from_library(load_library('mm.dll'))`` (see ``native_library.py``) or
the simulated one with ``MotionController.mock()``.
"""
import ctypes
from dataclasses import dataclass
from typing import Callable

from pymodaq_plugins_mockexamples.hardware.mock_dll_controller import (MM_CALLBACK, MM_Info, MockMotionLibrary, MM_OK,
                                                                       PORT, N_AXES)


class MotionControllerError(RuntimeError):
    """An error code returned by the library, with the message of the library"""


@dataclass
class ControllerInfo:
    name: str
    n_axes: int
    firmware: tuple[int, int]


class MotionController:
    """Handle of an opened controller and its axes (numbered from 0)"""
    n_axes = N_AXES

    def __init__(self, library, port: str = PORT):
        self._lib = library
        self._declare()
        self._handle = ctypes.c_void_p()
        self._check(self._lib.mm_open(port.encode(), ctypes.byref(self._handle)))
        self._listeners: list[Callable[[int, int], None]] = []
        self._callback = MM_CALLBACK(self._on_event)  # kept alive: the library keeps the pointer
        self._check(self._lib.mm_set_callback(self._handle, self._callback))

    @classmethod
    def mock(cls, speed: float = 25.) -> 'MotionController':
        """The controller on the simulated library (no DLL needed)"""
        return cls(MockMotionLibrary(speed))

    def _declare(self):
        lib = self._lib
        lib.mm_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
        lib.mm_close.argtypes = [ctypes.c_void_p]
        lib.mm_get_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(MM_Info)]
        lib.mm_move_abs.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
        lib.mm_get_position.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.mm_is_moving.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        lib.mm_stop.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.mm_home.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.mm_set_callback.argtypes = [ctypes.c_void_p, MM_CALLBACK]
        lib.mm_error_message.argtypes = [ctypes.c_int]
        lib.mm_error_message.restype = ctypes.c_char_p
        for name in ('mm_open', 'mm_close', 'mm_get_info', 'mm_move_abs', 'mm_get_position', 'mm_is_moving', 'mm_stop',
                     'mm_home', 'mm_set_callback'):
            getattr(lib, name).restype = ctypes.c_int

    def _check(self, code: int):
        if code != MM_OK:
            raise MotionControllerError(f'{self._lib.mm_error_message(code).decode()} (code {code})')

    def _on_event(self, axis: int, event: int):
        """Called by the library, from one of its threads"""
        for listener in list(self._listeners):
            listener(axis, event)

    def subscribe(self, listener: Callable[[int, int], None]):
        """``listener(axis, event)`` is called, from a thread of the library, when a move ends (see the EVENT_*)"""
        self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[int, int], None]):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def info(self) -> ControllerInfo:
        info = MM_Info()
        self._check(self._lib.mm_get_info(self._handle, ctypes.byref(info)))
        return ControllerInfo(info.name.decode(), info.n_axes, (info.firmware[0], info.firmware[1]))

    def position(self, axis: int) -> float:
        position = ctypes.c_double()
        self._check(self._lib.mm_get_position(self._handle, axis, ctypes.byref(position)))
        return position.value

    def is_moving(self, axis: int) -> bool:
        moving = ctypes.c_int()
        self._check(self._lib.mm_is_moving(self._handle, axis, ctypes.byref(moving)))
        return bool(moving.value)

    def move_abs(self, axis: int, position: float):
        """Start the move; the library calls back when it is over"""
        self._check(self._lib.mm_move_abs(self._handle, axis, position))

    def stop(self, axis: int):
        self._check(self._lib.mm_stop(self._handle, axis))

    def home(self, axis: int):
        """Start the homing; the library calls back when it is over"""
        self._check(self._lib.mm_home(self._handle, axis))

    def close(self):
        if self._handle.value is not None:
            self._lib.mm_close(self._handle)
            self._handle = ctypes.c_void_p()
        self._listeners.clear()


LIBRARY_NAMES = {'Windows': ['mm.dll'], 'Linux': ['libmm.so'], 'Darwin': ['libmm.dylib']}  # names of the (imaginary) DLL


def open_controller(port: str, library_path: str = '') -> MotionController:
    """The controller of the simulated library for the port ``MOCK``, else of the vendor library found by
    ``load_library`` (setting of the plugin, environment variable ``MM_LIBRARY``, system folders)"""
    if port == PORT:
        return MotionController.mock()
    from pymodaq_plugins_mockexamples.hardware.native_library import load_library
    return MotionController(load_library(LIBRARY_NAMES, path=library_path or None, env_var='MM_LIBRARY'), port)
