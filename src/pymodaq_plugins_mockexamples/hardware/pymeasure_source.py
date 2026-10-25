"""Recipe: a ``pymeasure`` driver for an instrument speaking SCPI-like text commands.

This is the recommended way to talk to a text-protocol instrument (serial, VISA, TCP): a few declarative lines give
named properties, validation of the values, and error checking, and the same driver can be reused by scripts and by
the PyMoDAQ plugin. Contribute it to ``pymeasure`` if the instrument is a commercial model. The points to copy:

- derive from ``SCPIMixin`` and ``Instrument``; ``control`` makes a read/write property, ``measurement`` a read-only one;
- ``validator`` and ``values`` reject out of range values before anything is sent;
- test the driver with ``ProtocolAdapter``: it checks the exact commands sent and answers from a script
  (see ``tests/test_cookbook_drivers.py``);
- ``MockAdapter`` below is the other kind of test double: it runs the commands on a simulated device, so that the
  plugin can be tried in the Dashboard without hardware.
"""
from typing import Optional

from pymeasure.adapters import Adapter
from pymeasure.instruments import Instrument, SCPIMixin
from pymeasure.instruments.validators import strict_range

from pymodaq_plugins_mockexamples.hardware.mock_instrument import MockInstrument


class CookbookSource(SCPIMixin, Instrument):
    """pymeasure driver of the simulated stage and voltmeter of ``MockInstrument``"""

    def __init__(self, adapter, name='Cookbook device', **kwargs):
        super().__init__(adapter, name, **kwargs)

    position = Instrument.control(
        'POS?', 'POS %g',
        """Control the position in mm: setting starts the motion, getting reads the present position""",
        validator=strict_range, values=[-100, 100], check_set_errors=True)

    voltage = Instrument.measurement('MEAS:VOLT?', """Measure the voltage in V""")

    def home(self):
        """Go to 0"""
        self.write('HOME')

    def stop(self):
        """Stop the motion where the stage is"""
        self.write('STOP')


class MockAdapter(Adapter):
    """A pymeasure adapter whose far end is a simulated ``MockInstrument``

    Parameters
    ----------
    device: MockInstrument, optional
        The simulated device, a new one by default
    """

    def __init__(self, device: Optional[MockInstrument] = None, **kwargs):
        super().__init__(**kwargs)
        self.device = device if device is not None else MockInstrument()
        self._answers = []

    def _write(self, command, **kwargs):
        answer = self.device.execute(command)
        if answer is not None:
            self._answers.append(answer)

    def _read(self, **kwargs):
        if not self._answers:
            raise TimeoutError('No answer from the simulated device')
        return self._answers.pop(0)

    def _read_bytes(self, count, break_on_termination=False, **kwargs):
        raise NotImplementedError('The simulated device speaks text only')
