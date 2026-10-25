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
A cookbook example of a device pattern: plugins (an actuator and a detector, 0D or 1D) with their driver in
`hardware/`, that run on a mock device and are meant to be copied and adapted. The camera recipe is the exception: it
is an existing mock plugin (`BSCamera`) completed to show the pattern.

**Hardware ROI**:
The region of the sensor read and binned by the camera itself, in sensor pixels; the image is smaller. Opposed to the
*software ROI* drawn in the viewer and applied by the plugin after the grab (`RoiStuff`).

**Calibrated axis**:
The axis sent with the data of a detector, in physical units (um, nm), as the instrument gives it. It can change
between two grabs (ROI, binning, central wavelength), so it is asked at every grab.
