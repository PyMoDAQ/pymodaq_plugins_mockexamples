# Mock examples

Words used in this package.

**Mock**:
A simulated device or instrument that behaves like the real one, without hardware (the package name, the `MOCK`
port or address of the cookbook recipes, the `Mock*` plugins and classes). In test-double vocabulary it is a *fake*,
a lightweight working implementation; it does not check how it is called, as a call-verifying mock would.
_Avoid_: using "fake" for the same thing, so the package speaks one language.

**Setup**:
A set of mock instruments that simulate one experiment together (beam steering, heater with PID, ...). Each
setup has an experiment file in `resources/`.

**Recipe**:
A cookbook example of a device pattern: an actuator and a 0D detector, with their driver in `hardware/`, that run
on a mock device and are meant to be copied and adapted.
