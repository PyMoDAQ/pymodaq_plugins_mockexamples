"""Recipe: a driver written directly on top of a serial port (RS-232, USB-serial).

Use this when the instrument speaks a text protocol on a serial line and no driver exists. If a ``pymeasure`` driver
can be written instead, prefer it (see ``pymeasure_source.py``): it gives named properties, validators and error
checking for free. The points to copy from here:

- the port is opened by the driver from a name, or given as an already open object (tests, simulation);
- one lock around every write/read pair, because the actuator and a detector can share the same driver (master/slave);
- a query always flushes the input buffer first, and an empty answer is a timeout, never a value;
- the device error queue is read after commands that can fail;
- ``close`` is safe to call twice.
"""
import threading
import time
from typing import Union


class SerialStageError(Exception):
    """The device reported an error, or did not answer"""


class SerialStage:
    """Driver of the simulated stage and voltmeter of ``MockInstrument`` through a serial line

    Parameters
    ----------
    port: str or serial-like object
        Name of the serial port (``COM3``, ``/dev/ttyUSB0``), or an object with the ``write``/``readline``/
        ``reset_input_buffer``/``close`` methods of ``serial.Serial``
    baudrate: int
        Only used when ``port`` is a name
    timeout: float
        Seconds to wait for an answer, only used when ``port`` is a name
    """
    termination = b'\r\n'

    def __init__(self, port: Union[str, object], baudrate: int = 9600, timeout: float = 1.):
        if isinstance(port, str):
            import serial  # imported here: the module can be read without pyserial installed
            port = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self._port = port
        self._lock = threading.RLock()

    def _write(self, command: str):
        self._port.write(command.encode('ascii') + self.termination)

    def _query(self, command: str) -> str:
        with self._lock:
            self._port.reset_input_buffer()
            self._write(command)
            answer = self._port.readline().decode('ascii').strip()
        if not answer:
            raise SerialStageError(f'No answer to {command!r}')
        return answer

    def _send(self, command: str):
        with self._lock:
            self._write(command)
            self.check_error()

    def check_error(self):
        """Raise ``SerialStageError`` with the oldest error of the device, if any"""
        answer = self._query('SYST:ERR?')
        code, _, message = answer.partition(',')
        if int(code) != 0:
            raise SerialStageError(f'Device error {answer}')

    def identity(self) -> str:
        return self._query('*IDN?')

    @property
    def position(self) -> float:
        """Position in mm"""
        return float(self._query('POS?'))

    def move_to(self, position: float):
        """Start the motion to ``position`` (mm) and return, the plugin polls ``position``"""
        self._send(f'POS {position:.4f}')

    def home(self, timeout: float = 10.):
        """Go to 0 and return when the stage is there (blocking homing)"""
        self._send('HOME')
        t_end = time.monotonic() + timeout
        while abs(self.position) > 0.005:
            if time.monotonic() > t_end:
                raise SerialStageError('Homing timeout')
            time.sleep(0.01)

    def stop(self):
        self._send('STOP')

    def read_voltage(self) -> float:
        """Voltage in V"""
        return float(self._query('MEAS:VOLT?'))

    def close(self):
        if getattr(self._port, 'is_open', False):
            self._port.close()
