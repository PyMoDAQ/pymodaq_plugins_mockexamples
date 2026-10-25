"""Calls to the real C library of the system with ``ctypes``: no vendor library needed to see the techniques.

Each function shows one thing a driver for a vendor DLL does: declare ``argtypes`` and ``restype``, receive a value
through a pointer (``byref``), give the library a Python function as a callback (``CFUNCTYPE``). They run on Linux,
macOS and Windows (``libc``, ``libm`` or ``ucrtbase``). See ``native_library.py`` for the loading and
``mock_dll_controller.py`` for the same techniques on a simulated vendor library.
"""
import ctypes
from typing import Callable, Sequence

from pymodaq_plugins_mockexamples.hardware.native_library import load_library

C_LIBRARY = {'Linux': ['libc.so.6', 'c'], 'Darwin': ['libc.dylib', 'c'], 'Windows': ['ucrtbase.dll']}
MATH_LIBRARY = {'Linux': ['libm.so.6', 'm'], 'Darwin': ['libm.dylib', 'm'], 'Windows': ['ucrtbase.dll']}


def string_length(text: str) -> int:
    """``size_t strlen(const char *s)``: arguments and return type declared, a Python str sent as bytes"""
    libc = load_library(C_LIBRARY)
    libc.strlen.argtypes = [ctypes.c_char_p]
    libc.strlen.restype = ctypes.c_size_t  # the default restype is a C int: wrong for a size_t on 64 bits
    return libc.strlen(text.encode('ascii'))


def split_mantissa_exponent(value: float) -> tuple[float, int]:
    """``double frexp(double x, int *exp)``: an output parameter, received through ``byref``"""
    libm = load_library(MATH_LIBRARY)
    libm.frexp.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_int)]
    libm.frexp.restype = ctypes.c_double
    exponent = ctypes.c_int()
    mantissa = libm.frexp(value, ctypes.byref(exponent))
    return mantissa, exponent.value


def sort_with_callback(values: Sequence[float], compare: Callable[[float, float], int]) -> list[float]:
    """``void qsort(void *base, size_t n, size_t size, int (*cmp)(const void *, const void *))``

    The library calls ``compare`` (a Python function) many times. The ``CFUNCTYPE`` object must stay alive while the
    library can call it: here it is a local variable that lives until ``qsort`` returns; a driver that gives a callback
    to a library that keeps it (a ``set_callback`` function) must store it in an attribute.
    """
    libc = load_library(C_LIBRARY)
    compare_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double))
    libc.qsort.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, compare_type]
    libc.qsort.restype = None

    array = (ctypes.c_double * len(values))(*values)
    libc.qsort(array, len(array), ctypes.sizeof(ctypes.c_double),
               compare_type(lambda a, b: compare(a[0], b[0])))
    return list(array)
