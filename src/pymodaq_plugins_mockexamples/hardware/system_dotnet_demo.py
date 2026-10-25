"""Calls to the real .NET libraries of the runtime with ``pythonnet``: no vendor assembly needed to see the techniques.

Each function shows one thing a driver for a vendor assembly does: receive an ``out`` parameter, catch a .NET
exception, pass a typed array or a generic collection, give a Python function to an event raised by another thread,
dispose an object. They run on the .NET Framework (Windows) and on .NET 6+ (``coreclr``). See ``dotnet_runtime.py``
for the start of the runtime and ``mock_dotnet_controller.py`` for the same techniques on a simulated assembly.
"""
import threading
from typing import Callable, Optional, Sequence

from pymodaq_plugins_mockexamples.hardware.dotnet_runtime import load_dotnet, load_assembly


def parse_integer(text: str) -> Optional[int]:
    """``static bool Int32.TryParse(string s, out int result)``: ``pythonnet`` returns ``(bool, result)``"""
    load_dotnet()
    from System import Int32
    ok, value = Int32.TryParse(text)
    return value if ok else None


def parse_integer_or_raise(text: str) -> int:
    """``static int Int32.Parse(string s)`` throws a ``FormatException``: catch the .NET type, read its ``Message``"""
    load_dotnet()
    from System import Int32, FormatException
    try:
        return Int32.Parse(text)
    except FormatException as exc:
        raise ValueError(exc.Message) from None  # str(exc) also holds the .NET stack trace


def sum_of_list(values: Sequence[float]) -> float:
    """A generic collection: ``List[float]`` is ``List<double>`` (the type is given between brackets)"""
    load_assembly(['System.Collections'])
    from System.Collections.Generic import List
    numbers = List[float]()
    for value in values:
        numbers.Add(value)
    return sum(numbers)  # a .NET collection is iterable


def bytes_through_a_stream(data: bytes) -> bytes:
    """A typed array and an ``IDisposable``: ``Array[Byte]`` is ``byte[]``, ``Dispose`` is called in ``finally``"""
    load_dotnet()
    from System import Array, Byte
    from System.IO import MemoryStream
    stream = MemoryStream()
    try:
        buffer = Array[Byte](data)
        stream.Write(buffer, 0, buffer.Length)
        return bytes(stream.ToArray())
    finally:
        stream.Dispose()


def call_back_from_another_thread(on_elapsed: Callable[[], None], delay_ms: int = 10) -> Callable[[], None]:
    """An event raised by a thread of the runtime: ``timer.Elapsed += function``

    ``System.Timers.Timer`` raises ``Elapsed`` from a thread of the .NET thread pool, as a vendor assembly raises its
    own events. ``on_elapsed`` is converted to a delegate and called in that thread: it must be thread safe, and
    only emit a Qt signal. The function returned stops and releases the timer: call it, or the event and the delegate
    stay alive.
    """
    load_assembly(['System.ComponentModel.TypeConverter', 'System'])  # the assembly that holds Timer depends on the runtime
    from System.Timers import Timer
    timer = Timer(delay_ms)
    timer.AutoReset = False

    def handler(sender, args):
        on_elapsed()

    timer.Elapsed += handler

    def release():
        timer.Stop()
        timer.Elapsed -= handler  # the very same object given to +=
        timer.Dispose()

    timer.Start()
    return release


def thread_of_the_event(delay_ms: int = 10, timeout: float = 5.) -> threading.Thread:
    """The Python thread in which the event handler was called (not the main one)"""
    done = threading.Event()
    threads = []

    def on_elapsed():
        threads.append(threading.current_thread())
        done.set()

    release = call_back_from_another_thread(on_elapsed, delay_ms)
    try:
        if not done.wait(timeout):
            raise TimeoutError('The event was not raised')
    finally:
        release()
    return threads[0]
