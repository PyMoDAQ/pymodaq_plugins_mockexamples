"""One pure python instrument, and the three transports used by the cookbook recipes to talk to it.

``MockInstrument`` stands for the firmware of a small stage with a voltmeter. It understands SCPI-like text commands,
so the same simulated device is reached the three ways a real one would be:

- ``MockSerialPort``: bytes, like a ``serial.Serial`` object (recipe ``CookbookSerial``),
- ``MockVisaResource``: text, like a ``pyvisa`` resource (recipe ``CookbookVisa``),
- ``MockAdapter``: a ``pymeasure`` adapter (recipe ``CookbookPymeasure``, in ``pymeasure_source.py``).

None of them needs hardware nor a driver. In a plugin, the port name ``MOCK`` selects them.
"""
import time
from typing import Optional


class MockInstrument:
    """Firmware of the simulated device

    Commands (case insensitive, mnemonics may be abbreviated or written in full: ``MEAS:VOLT?`` or
    ``MEASURE:VOLTAGE?``)::

        *IDN?            identification string
        POS <x>          move to x (mm) at ``speed``; returns at once
        POS?             present position (mm), moving or not
        HOME             go to 0
        STOP             stop where the stage is
        MEAS:VOLT?       voltage (V) = 0.5 + 0.1 * position
        SYST:ERR?        oldest error as ``code,"message"``, ``0,"No error"`` if none

    Parameters
    ----------
    speed: float
        Speed of the simulated stage in mm/s
    """
    IDN = 'PyMoDAQ,CookbookDevice,0001,1.0'

    def __init__(self, speed: float = 100.):
        self.speed = speed
        self.commands = []  # every received command, for the tests
        self._errors = []
        self._start = 0.
        self._target = 0.
        self._t0 = time.monotonic()

    @property
    def position(self) -> float:
        """Position in mm: linear motion from the start point to the target"""
        distance = self._target - self._start
        travelled = min(abs(distance), self.speed * (time.monotonic() - self._t0))
        return self._start + (travelled if distance >= 0 else -travelled)

    def _set_target(self, target: float):
        self._start = self.position
        self._target = target
        self._t0 = time.monotonic()

    @staticmethod
    def _normalise(header: str) -> str:
        """``measure:voltage?`` -> ``MEA:VOL?``: three letters per mnemonic cover short and long SCPI forms"""
        parts = header.strip().lstrip(':').upper().split(':')
        return ':'.join(part[:3] if not part.endswith('?') else part[:-1][:3] + '?' for part in parts)

    def execute(self, line: str) -> Optional[str]:
        """Run one command line (without terminator); returns the answer of a query, None otherwise"""
        self.commands.append(line)
        header, _, argument = line.strip().partition(' ')
        header = self._normalise(header) if not header.startswith('*') else header.upper()
        try:
            if header == '*IDN?':
                return self.IDN
            if header == '*RST':
                self._set_target(0.)
            elif header == 'POS':
                self._set_target(float(argument))
            elif header == 'POS?':
                return f'{self.position:.4f}'
            elif header == 'HOM':
                self._set_target(0.)
            elif header == 'STO':
                self._set_target(self.position)
            elif header == 'MEA:VOL?':
                return f'{0.5 + 0.1 * self.position:.4f}'
            elif header == 'SYS:ERR?':
                code, message = self._errors.pop(0) if self._errors else (0, 'No error')
                return f'{code},"{message}"'
            else:
                self._errors.append((-113, 'Undefined header'))
        except ValueError:
            self._errors.append((-104, 'Data type error'))
        return None


class MockSerialPort:
    """The part of ``serial.Serial`` used by drivers, in front of a ``MockInstrument``

    Commands end with ``\\n`` (``\\r`` is ignored), answers end with ``\\r\\n``. An empty answer from ``readline`` means
    that the device did not answer before the timeout, as with the real class.
    """
    def __init__(self, device: Optional[MockInstrument] = None, timeout: float = 1.):
        self.device = device if device is not None else MockInstrument()
        self.timeout = timeout
        self.is_open = True
        self._pending = b''
        self._answers = b''

    def write(self, data: bytes) -> int:
        self._pending += data
        while b'\n' in self._pending:
            line, _, self._pending = self._pending.partition(b'\n')
            answer = self.device.execute(line.decode().strip())
            if answer is not None:
                self._answers += answer.encode() + b'\r\n'
        return len(data)

    def readline(self) -> bytes:
        line, sep, self._answers = self._answers.partition(b'\n')
        return line + sep

    @property
    def in_waiting(self) -> int:
        return len(self._answers)

    def reset_input_buffer(self):
        self._answers = b''

    def close(self):
        self.is_open = False


class MockVisaResource:
    """The part of a ``pyvisa`` message based resource used by drivers, in front of a ``MockInstrument``"""
    def __init__(self, device: Optional[MockInstrument] = None):
        self.device = device if device is not None else MockInstrument()
        self.timeout = 1000  # ms, as in pyvisa
        self.read_termination = '\n'
        self.write_termination = '\n'
        self.is_open = True
        self._answers = []

    def write(self, message: str) -> int:
        answer = self.device.execute(message)
        if answer is not None:
            self._answers.append(answer)
        return len(message)

    def read(self) -> str:
        if not self._answers:
            raise TimeoutError('VI_ERROR_TMO: no answer from the device')
        return self._answers.pop(0)

    def query(self, message: str) -> str:
        self.write(message)
        return self.read()

    def close(self):
        self.is_open = False
