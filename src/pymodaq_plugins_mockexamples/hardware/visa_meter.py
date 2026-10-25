"""Recipe: a driver written directly on top of ``pyvisa`` (GPIB, USB-TMC, TCP/IP, serial instruments).

Use this for an instrument that speaks SCPI on a VISA resource when a ``pymeasure`` driver is not worth writing
(see ``pymeasure_source.py`` otherwise). The points to copy from here:

- the resource is opened from its address (``TCPIP0::192.168.0.5::INSTR``) or given already open (tests, simulation);
- terminations and timeout are set explicitly, never left to the defaults of the backend;
- ``query`` is used for questions, ``write`` for commands, and the error queue is read after commands;
- ``close`` is safe to call twice.
"""
import time
from typing import Union


class VisaMeterError(Exception):
    """The device reported an error"""


class VisaMeter:
    """Driver of the simulated stage and voltmeter of ``MockInstrument`` through a VISA resource

    Parameters
    ----------
    resource: str or pyvisa-like resource
        VISA address, or an object with the ``write``/``query``/``close`` methods of a pyvisa message resource
    timeout: int
        Milliseconds, set on the resource
    """

    def __init__(self, resource: Union[str, object], timeout: int = 2000):
        if isinstance(resource, str):
            import pyvisa  # imported here: the module can be read without pyvisa installed
            resource = pyvisa.ResourceManager().open_resource(resource)
            resource.read_termination = '\n'
            resource.write_termination = '\n'
        resource.timeout = timeout
        self._resource = resource

    def check_error(self):
        """Raise ``VisaMeterError`` with the oldest error of the device, if any"""
        answer = self._resource.query('SYST:ERR?').strip()
        if int(answer.partition(',')[0]) != 0:
            raise VisaMeterError(f'Device error {answer}')

    def identity(self) -> str:
        return self._resource.query('*IDN?').strip()

    @property
    def position(self) -> float:
        """Position in mm"""
        return float(self._resource.query('POS?'))

    def move_to(self, position: float):
        """Start the motion to ``position`` (mm) and return"""
        self._resource.write(f'POS {position:.4f}')
        self.check_error()

    def home(self, timeout: float = 10.):
        """Go to 0 and return when the stage is there (blocking homing)"""
        self._resource.write('HOME')
        self.check_error()
        t_end = time.monotonic() + timeout
        while abs(self.position) > 0.005:
            if time.monotonic() > t_end:
                raise VisaMeterError('Homing timeout')
            time.sleep(0.01)

    def stop(self):
        self._resource.write('STOP')
        self.check_error()

    def read_voltage(self) -> float:
        """Voltage in V"""
        return float(self._resource.query('MEAS:VOLT?'))

    def close(self):
        if getattr(self._resource, 'is_open', True):
            self._resource.close()
